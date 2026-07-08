import { useState } from "react"
import { Card, Image, Button, DataList, } from "@chakra-ui/react";
import { useMetadata } from "./MetadataProvider";
import { UpdateKeywordsDialog } from "./UpdateKeywordsDialog";
import { Metadata } from "../api";


export default function MetadataCard({ metadata_in }: { metadata_in: Metadata }) {
    const { url } = useMetadata();
    const image_url = `${url}/image/${metadata_in.filename}`
    const [metadata, setMetadata] = useState<Metadata>(metadata_in)

    const fetchMetadata = async (refresh: boolean = false) => {

        // setMetadata({ id: image_name, filename: image_name, description: "", keywords: [], title: "Refreshing..." } as Metadata)
        const response = await fetch(`${url}metadata/${metadata.id}?refresh=${refresh}`)
        const fetched_metadata = await response.json()
        setMetadata(fetched_metadata.data)
    }


    return (
        <Card.Root maxW="l" h="100%">
            <Image
                src={image_url}
                alt="Image"
                p={2}
                rounded="xl"
                maxH={200}
                maxW="100%"
                objectFit="contain"
            />
            <Card.Body>
                <Card.Title>{metadata.title || metadata.filename || "Unknown"}</Card.Title>
                <Card.Description>
                    {metadata.description || "No description"}
                </Card.Description>
                <DataList.Root orientation="vertical"
                    style={{
                        marginTop: "1.0rem",
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
                    <DataList.Item >
                        <DataList.ItemLabel><b>Creation date:</b></DataList.ItemLabel>
                        <DataList.ItemValue>{metadata.create_date || "Unknown"}</DataList.ItemValue>
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


