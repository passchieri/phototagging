/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';
export class ImagesService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Available Images
     * Return a list of images that are available, but not yet have metadata
     * @returns string Successful Response
     * @throws ApiError
     */
    public scan(): CancelablePromise<Array<string>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/scan',
        });
    }
    /**
     * List Images
     * Returns a paginated list of image filenames in the root directory,
     * sorted by modification time (newest first).
     * @returns string Successful Response
     * @throws ApiError
     */
    public getImages(): CancelablePromise<Array<string>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/images',
        });
    }
    /**
     * Get Image
     * @param name Filename of the image to get
     * @returns any Successful Response
     * @throws ApiError
     */
    public getImage(
        name: string,
    ): CancelablePromise<any> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/image/{name}',
            path: {
                'name': name,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
