import { configService } from '../services/configService';

export interface StorageConfig {
    bucketName: string;
    region: string;
}

export const getStorageConfig = (): StorageConfig => {
    try {
        const runtimeConfig = configService.getConfig();
        return {
            bucketName: runtimeConfig.s3BucketName,
            region: runtimeConfig.region
        };
    } catch (error) {
        console.warn('Failed to load runtime config, using default:', error);
        return {
            bucketName: '',
            region: 'us-east-1'
        };
    }
}
