/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { KeywordsUpdateRequest } from '../models/KeywordsUpdateRequest';
import type { Metadata } from '../models/Metadata';
import type { Result } from '../models/Result';
import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';
export class MetadataService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Get All Metadata
     * @returns Metadata Successful Response
     * @throws ApiError
     */
    public getMetadatas(): CancelablePromise<Array<Metadata>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/metadata',
        });
    }
    /**
     * Get Image Metadata
     * @param id id of a metadata entry
     * @returns Metadata Successful Response
     * @throws ApiError
     */
    public getMetadata(
        id: string,
    ): CancelablePromise<Metadata> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/metadata/{id}',
            path: {
                'id': id,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Patch Image Metadata
     * @param id ID of the metadata to update
     * @param requestBody
     * @returns Metadata Successful Response
     * @throws ApiError
     */
    public patchMetadata(
        id: string,
        requestBody: KeywordsUpdateRequest,
    ): CancelablePromise<Metadata> {
        return this.httpRequest.request({
            method: 'PATCH',
            url: '/metadata/{id}',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Image Metadata
     * @param id ID of the metadata to delete
     * @returns Result Successful Response
     * @throws ApiError
     */
    public deleteMetadata(
        id: string,
    ): CancelablePromise<Result> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/metadata/{id}',
            path: {
                'id': id,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Post Image Metadata
     * @param name Filename of the image to create metadata for
     * @param includeKeywords List of keywords to include in the metadata
     * @param excludeKeywords List of keywords to exclude from the metadata
     * @returns Metadata Successful Response
     * @throws ApiError
     */
    public getMetadataByName(
        name: string,
        includeKeywords?: (Array<string> | null),
        excludeKeywords?: (Array<string> | null),
    ): CancelablePromise<Metadata> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/metadata/{name}',
            path: {
                'name': name,
            },
            query: {
                'include_keywords': includeKeywords,
                'exclude_keywords': excludeKeywords,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
