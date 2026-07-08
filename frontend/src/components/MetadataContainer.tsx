import { Grid, GridItem, Container } from "@chakra-ui/react"
import MetadataCard from "./MetadataCard";
import { useMetadata } from "./MetadataProvider";



export default function MetadataContainer() {
    const { 
        filteredMetadataSet,
    } = useMetadata()

    return (
        <Container maxW="container.xl">
            <Grid templateColumns="repeat(auto-fit, minmax(300px, 1fr))" gap={5} padding={5}>
                {filteredMetadataSet.map((metadata) => (
                    <GridItem key={metadata.id} style={{ alignItems: "stretch" }}>
                        <MetadataCard metadata_in={metadata} />
                    </GridItem>
                ))}
            </Grid>
        </Container>
    )
}
