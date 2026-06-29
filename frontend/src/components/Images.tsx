import { Grid, GridItem, Container } from "@chakra-ui/react"
import ImageCard from "./ImageCard";
import { useImages } from "./ImageProvider";



export default function Images() {
    const { 
        filteredMetadataSet,
    } = useImages()

    return (
        <Container maxW="container.xl">
            <Grid templateColumns="repeat(auto-fit, minmax(300px, 1fr))" gap={5} padding={5}>
                {filteredMetadataSet.map((metadata) => (
                    <GridItem key={metadata.id} style={{ alignItems: "stretch" }}>
                        <ImageCard metadata_in={metadata} />
                    </GridItem>
                ))}
            </Grid>
        </Container>
    )
}
