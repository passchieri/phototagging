import { useEffect, useRef, useState } from "react"
import { Card, Image, Button, DataList, Dialog, Portal, CloseButton } from "@chakra-ui/react";
import { ImageMetadata } from "./interfaces";
import { useImages } from "./ImageProvider";
import { UpdateKeywordsDialog } from "./UpdateKeywordsDialog";


export default function ImageCard({ metadata_in }: { metadata_in: ImageMetadata }) {
    const { url } = useImages();
    const image_url = `${url}image/${metadata_in.filename}`
    const [metadata, setMetadata] = useState<ImageMetadata>(metadata_in)

    const fetchMetadata = async (refresh: boolean = false) => {
        // setMetadata({ id: image_name, filename: image_name, description: "", keywords: [], title: "Refreshing..." } as ImageMetadata)
        const response = await fetch(`${url}metadata/${metadata.id}?refresh=${refresh}`)
        const fetched_metadata = await response.json()
        setMetadata(fetched_metadata.data)
    }


    return (
        <Card.Root maxW="l" h="100%">
            <Image src={image_url} alt="Image" p={2} rounded="xl" />
            <Card.Body>
                <Card.Title>{metadata.title || metadata.filename || "Unknown"}</Card.Title>
                <Card.Description>
                    {metadata.description || "No description"}
                </Card.Description>
                <p>&nbsp;</p>
                <DataList.Root orientation="vertical"
                    style={{
                        // display: "grid",
                        // gridTemplateColumns: "max-content 1fr",
                        rowGap: "1.0rem",
                        // columnGap: "1rem",
                        // alignItems: "start",
                    }}
                >
                    <DataList.Item marginBlockEnd={2}>
                        <DataList.ItemLabel><b>Keywords:</b></DataList.ItemLabel>
                        <DataList.ItemValue>{metadata.keywords?.join(", ") || "No keywords"}</DataList.ItemValue>
                    </DataList.Item>
                    <DataList.Item >
                        <DataList.ItemLabel><b>Filename:</b></DataList.ItemLabel>
                        <DataList.ItemValue>{metadata.filename || "Unknown"}</DataList.ItemValue>
                    </DataList.Item>
                    <DataList.Item >
                        <DataList.ItemLabel><b>Path:</b></DataList.ItemLabel>
                        <DataList.ItemValue>{metadata.full_path || "Unknown"}</DataList.ItemValue>
                    </DataList.Item>
                </DataList.Root>
            </Card.Body>
            <Card.Footer>
                <Button variant="outline" onClick={() => fetchMetadata(true)}>Refresh</Button>
                <UpdateKeywordsDialog metadata={metadata} url={url} children={undefined} setMetadata={setMetadata} />
            </Card.Footer>
        </Card.Root >
    )
}


