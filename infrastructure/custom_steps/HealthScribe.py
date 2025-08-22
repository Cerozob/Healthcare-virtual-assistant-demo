from aws_cdk import aws_stepfunctions_tasks as sfn_tasks, aws_iam as iam, aws_s3 as s3
from aws_cdk import aws_stepfunctions as sfn, Duration
from constructs import Construct


def buildStepChain(
    scope: Construct,
    id: str,
    *,
    output_bucket: s3.Bucket,
    healthscribe_role: iam.Role,
    **kwargs,
) -> sfn.Chain:
    """
    Complete HealthScribe workflow chain that includes:
    1. Starting the job
    2. Polling for completion
    3. Moving outputs to patient-specific prefix
    4. Cleaning up temporary files

    disclaimer: we assume JSONata, not JSONPath
    """

    # Start HealthScribe job
    healthscribe_start = sfn_tasks.CallAwsService.jsonata(
        scope,
        f"{id}Start",
        service="transcribe",
        action="startMedicalScribeJob",
        iam_resources=["*"],
        parameters={
            "DataAccessRoleArn": healthscribe_role.role_arn,
            "Media": {"MediaFileUri": '{% "s3://" & $bucket & "/" & $key %}'},
            "MedicalScribeJobName": '{% $unique_id & "_healthscribe_job" %}',
            "OutputBucketName": output_bucket.bucket_name,
            "Settings": {
                "ShowSpeakerLabels": True,
                "MaxSpeakerLabels": 3,
                "ChannelIdentification": False,
                "ClinicalNoteGenerationSettings": {
                    "NoteTemplate": "HISTORY_AND_PHYSICAL"
                },
            },
        },
        assign={
            "healthscribe_job_name": "{% $states.result.MedicalScribeJob.MedicalScribeJobName %}",
            "healthscribe_job_status": "{% $states.result.MedicalScribeJob.MedicalScribeJobStatus %}",
            "output_bucket": '{% "' + output_bucket.bucket_name + '" %}',
        },
    )

    # Wait for job to process
    healthscribe_wait = sfn.Wait(
        scope,
        f"{id}Wait",
        time=sfn.WaitTime.duration(Duration.seconds(30)),
    )

    # Check job status
    healthscribe_check = sfn_tasks.CallAwsService.jsonata(
        scope,
        f"{id}Check",
        service="transcribe",
        action="getMedicalScribeJob",
        iam_resources=["*"],
        parameters={"MedicalScribeJobName": "{% $healthscribe_job_name %}"},
        assign={
            "healthscribe_job_status": "{% $states.result.MedicalScribeJob.MedicalScribeJobStatus %}",
            # we do NOT use the healthscribe output paths because the are the full url https://region.amazonaws.com/bucketname/key/file.json.
            # its easier to just manually build the path and wait for the COMPLETED flag
            "healthscribe_summary_key": '{% $healthscribe_job_name & "/summary.json" %}',
            "healthscribe_transcript_key": '{% $healthscribe_job_name & "/transcript.json" %}',
        },
    )

    file_metadata_spec = {
        "source-file": "{% $key %}",
        "healthscribe-job": "{% $healthscribe_job_name %}",
        "patient_id": "{% $patient_id %}",
    }

    # Copy both files in parallel and then clean up
    copy_files = (
        sfn.Parallel(
            scope,
            f"{id}CopyFiles",
            comment="Copy HealthScribe outputs to patient-specific prefix",
        )
        .branch(
            # Copy clinical note
            sfn_tasks.CallAwsService.jsonata(
                scope,
                f"{id}CopyClinicalNote",
                service="s3",
                action="copyObject",
                iam_resources=[f"{output_bucket.bucket_arn}/*"],
                parameters={
                    "Bucket": "{% $output_bucket %}",
                    "Key": '{%  $encodeUrlComponent($patient_id & "/healthscribe/" & $unique_id & "/" & "summary.json") %}',
                    "CopySource": '{% $encodeUrlComponent($output_bucket & "/" & $healthscribe_summary_key) %}',
                    "MetadataDirective": "REPLACE",
                    "Metadata": file_metadata_spec,
                },
            )
        )
        .branch(
            # Copy transcript
            sfn_tasks.CallAwsService.jsonata(
                scope,
                f"{id}CopyTranscript",
                service="s3",
                action="copyObject",
                iam_resources=[f"{output_bucket.bucket_arn}/*"],
                parameters={
                    "Bucket": "{% $output_bucket %}",
                    "Key": '{% $encodeUrlComponent($patient_id & "/healthscribe/" & $unique_id & "/" & "transcript.json") %}',
                    "CopySource": '{% $encodeUrlComponent($output_bucket & "/" & $healthscribe_transcript_key) %}',
                    "MetadataDirective": "REPLACE",
                    "Metadata": file_metadata_spec,
                },
            )
        )
    )

    # Delete original HealthScribe outputs
    delete_outputs = sfn_tasks.CallAwsService.jsonata(
        scope,
        f"{id}DeleteOutputs",
        service="s3",
        action="deleteObjects",
        iam_resources=[f"{output_bucket.bucket_arn}/*"],
        parameters={
            "Bucket": output_bucket.bucket_name,
            "Delete": {
                "Objects": [
                    {
                        "Key": "{% $encodeUrlComponent($healthscribe_summary_key) %}",
                    },
                    {
                        "Key": "{% $encodeUrlComponent($healthscribe_transcript_key) %}",
                    },
                ]
            },
        },
    )

    # Chain copy and cleanup
    move_and_cleanup = copy_files.next(delete_outputs)

    # Failure state
    healthscribe_failed = sfn.Fail(
        scope, f"{id}Failed", comment="HealthScribe job failed"
    )

    # Choice logic for job status
    healthscribe_choice = (
        sfn.Choice(scope, f"{id}Choice")
        .when(
            sfn.Condition.jsonata('{% $healthscribe_job_status = "COMPLETED" %}'),
            move_and_cleanup,
        )
        .when(
            sfn.Condition.jsonata('{% $healthscribe_job_status = "FAILED" %}'),
            healthscribe_failed,
        )
    )

    # Create the polling loop - reuse the same wait and check states
    polling_loop = healthscribe_wait.next(healthscribe_check).next(healthscribe_choice)

    # Set the otherwise condition to loop back to the same wait state
    healthscribe_choice.otherwise(polling_loop)

    # The main flow starts the job and enters the polling loop
    definition = healthscribe_start.next(polling_loop)
    return definition
