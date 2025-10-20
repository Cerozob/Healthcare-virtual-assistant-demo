import { configService } from '../services/configService';

export interface storageConfig {
    bucketName: string;
    region: string;
}

export const getStorageConfig = (): storageConfig => {
   try {
        const runtimeConfig = configService.getConfig();
        return {
            bucketName: runtimeConfig.s3BucketName as string,
            region: runtimeConfig.region || 'us-east-1'
        };
    } catch (error) {
        console.warn('Failed to load runtime config, using default:', error);
        return {
            bucketName: '',
            region: 'us-east-1'
        };
    }
}
