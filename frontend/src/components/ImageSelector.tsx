import { Field, Flex, FlexProps, Input } from "@chakra-ui/react";
import { useImages } from "./ImageProvider";


export function ImageSelector(props: FlexProps) {
    const { fileFilter, setFileFilter, keywordFilter, setKeywordFilter } = useImages();

    return (
        <Flex {...props} direction="horizontal" flexFlow="initial" gap={3} mt={3} mb={3}>
            <Field.Root orientation="vertical" width={300}>
                <Field.Label>File</Field.Label>
                <Input padding={2} variant="outline" flex="1" placeholder="File name" value={fileFilter} onChange={(e) => setFileFilter(e.target.value)} />
            </Field.Root>
            <Field.Root orientation="vertical" width={300}>
                <Field.Label>Keyword</Field.Label>
                <Input padding={2} variant="outline" flex="1" placeholder="Keyword" value={keywordFilter} onChange={(e) => setKeywordFilter(e.target.value)} />
            </Field.Root>
        </Flex>
    )
}

