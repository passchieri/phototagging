import { useEffect } from "react"
import { Card, Image, DataList, } from "@chakra-ui/react";
import { useMetadata } from "./MetadataProvider";
import { UpdateKeywordsDialog } from "./UpdateKeywordsDialog";
import { Metadata } from "../api";


export default function MetadataCard({ id }: { id: string }) {
    const { url, client, updateMetadataSet, metadataSet } = useMetadata();

    const metadata=metadataSet[id];
    if (!metadata) return (<></>);

    const image_url = `${url}/image/${metadata.filename}`


    useEffect(() => { 

    }, [metadataSet])

    function update(metadata: Metadata) {
        updateMetadataSet(metadata)
    }

    return (
        <Card.Root maxW="s" h="100%">
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
                        <DataList.ItemValue>{metadata.keywords?.sort((a,b)=>a.localeCompare(b)).join(", ") || "No keywords"}</DataList.ItemValue>
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
                {/* <Button variant="outline" onClick={() => fetchMetadata(true)}>Refresh</Button> */}
                <UpdateKeywordsDialog metadata={metadata} image_url={image_url} children={undefined} setMetadata={update} client={client} />
            </Card.Footer>
        </Card.Root >
    )
}


