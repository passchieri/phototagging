import { Box, BoxProps, Flex, FlexProps, HTMLChakraProps } from "@chakra-ui/react";
import { MetadataSelector } from "./MetadataSelector";
import MetadataContainer from "./MetadataContainer";
import Pagination from "./Pagination"

export default function MetadataPage() {
    return (<Flex direction = "column" height="100%" >
        <Box flex="0 0 auto">
            <MetadataSelector m={5} />
        </Box>

        {/* Body: fills remainder, scrolls if needed */}
        <Box flex="1 1 auto" overflowY="auto">
            <MetadataContainer />
        </Box>
        <Box flex="0 0 auto">
            <Pagination m={5} />
        </Box>
    </Flex>)
}