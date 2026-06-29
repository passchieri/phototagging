import { Button, CloseButton, Dialog, DialogRootProps, Portal, Image } from "@chakra-ui/react";
import KeywordsEditor from "./KeywordsEditor";
import { Dispatch, SetStateAction, useRef, useState } from "react";
import { ImageMetadata } from "./interfaces";

interface UpdateKeywordsProps extends DialogRootProps {
    metadata: ImageMetadata;
    url: string;
    setMetadata: Dispatch<SetStateAction<ImageMetadata>>
}
export function UpdateKeywordsDialog({ metadata, url, setMetadata, ...props }: UpdateKeywordsProps) {
    const updateRef = useRef<HTMLButtonElement>(null);
    const [updated_keywords, setUpdatedKeywords] = useState<string[]>([])
    const image_url = `${url}image/${metadata.filename}`

    const update_keywords = async () => {
        // Here you would send the updated keywords to the backend
        console.log("Updated keywords for", metadata.filename, ":", updated_keywords)
        // After updating, you might want to refresh the metadata
        const response = await fetch(`${url}metadata/${metadata.id}`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ keywords: updated_keywords })
        })
        if (response.ok) {
            const fetched_metadata = await response.json()
            setMetadata(fetched_metadata.data)
        }
    }

    return (
        <Dialog.Root {...props} key={metadata.id || -1}>
            <Dialog.Trigger asChild>
                <Button variant="outline">Update</Button>
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
                            <Image src={image_url} alt="Image" />
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