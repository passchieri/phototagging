import { Button, CloseButton, Dialog, DialogRootProps, Portal, Image, VStack, HStack } from "@chakra-ui/react";
import KeywordsEditor from "./KeywordsEditor";
import { useRef, useState } from "react";
import { Metadata, MetadataService } from "../api";

interface UpdateKeywordsProps extends DialogRootProps {
    metadata: Metadata;
    image_url: string;
    setMetadata: (metadata: Metadata) => void;
    client: MetadataService
}
export function UpdateKeywordsDialog({ metadata, image_url, setMetadata, client, ...props }: UpdateKeywordsProps) {
    const updateRef = useRef<HTMLButtonElement>(null);
    const [updated_keywords, setUpdatedKeywords] = useState<string[]>([])

    const update_keywords = async () => {
        // Here you would send the updated keywords to the backend
        console.log("Updated keywords for", metadata.filename, ":", updated_keywords)
        // After updating, you might want to refresh the metadata
        if (!metadata.id) return;
        const response = await client.patchMetadata(metadata.id, { keywords: updated_keywords })
        setMetadata(response)
    }

    return (
        <Dialog.Root {...props} key={metadata.id || -1}>
            <Dialog.Trigger asChild>
                <Button variant="outline">Edit</Button>
            </Dialog.Trigger>
            <Portal>
                <Dialog.Backdrop />
                <Dialog.Positioner>
                    <Dialog.Content
                        onKeyDown={(e) => {
                            console.log(e.key);
                            if (e.key === "Enter") {
                                e.preventDefault(); // prevents form submit or bubbling
                                updateRef.current?.click();
                            }
                        }}
                    >
                        <Dialog.Header>
                            <Dialog.Title>Update Metadata for {metadata.filename}</Dialog.Title>
                        </Dialog.Header>
                        <Dialog.Body>
                            <HStack justify="center" width="100%">
                                <Image
                                    src={image_url}
                                    alt="Image"
                                    p={2}
                                    rounded="xl"
                                    maxH={200}
                                    maxW="100%"
                                    objectFit="contain"
                                />
                            </HStack>
                            <KeywordsEditor metadata={metadata} setUpdatedKeywords={setUpdatedKeywords} />
                        </Dialog.Body>
                        <Dialog.Footer>
                            <Dialog.ActionTrigger asChild>
                                <span ref={updateRef}>
                                    <Button variant="solid" onClick={update_keywords}>Update</Button></span>
                            </Dialog.ActionTrigger>
                            <Dialog.ActionTrigger asChild>
                                <Button variant="outline">Cancel</Button>
                            </Dialog.ActionTrigger>
                        </Dialog.Footer>
                        <Dialog.CloseTrigger asChild>
                            <CloseButton />
                        </Dialog.CloseTrigger>
                    </Dialog.Content>
                </Dialog.Positioner>
            </Portal>
        </Dialog.Root>

    )
}