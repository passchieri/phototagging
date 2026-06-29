import { Button, Checkbox, Field, Flex, Group, Text, Input, Stack } from "@chakra-ui/react";
import { ImageMetadata } from "./interfaces";
import { useState } from "react";

export default function KeywordsEditor({ metadata, setUpdatedKeywords }: { metadata: ImageMetadata | null; setUpdatedKeywords: React.Dispatch<React.SetStateAction<string[]>> }) {

    const [allKeywords, updateAllKeywords] = useState<string[]>(metadata?.keywords || [])
    allKeywords.sort()

    const [crossedKeywords, updatedCrossedKeywords] = useState<string[]>([])

    const toggleKeywordCrossing = (keyword: string) => {
        // If the keyword is already crossed, uncross it; otherwise, cross it
        const crossed = crossedKeywords.includes(keyword)
            ? crossedKeywords.filter(k => k !== keyword)
            : [...crossedKeywords, keyword];
        updatedCrossedKeywords(crossed);
        setUpdatedKeywords(allKeywords.filter(k => !crossed.includes(k)));
    }

    const addKeyword = () => {
        const kw = newKeyword.trim();
        if (kw === "") return;
        if (!allKeywords.includes(kw)) {
            updateAllKeywords([...allKeywords, kw]);
        } else if (crossedKeywords.includes(kw)) {
            toggleKeywordCrossing(kw);
        }
        setNewKeyword("");
        setUpdatedKeywords([...allKeywords, kw].filter(k => !crossedKeywords.includes(k)));
    }
    
    const [newKeyword, setNewKeyword] = useState("");

    return (
        <Stack>
            <Text marginTop="6" fontWeight="semibold" fontSize="md">Keywords</Text>
            <Flex direction="row" wrap="wrap" gap={1}>
                {allKeywords.map((keyword,index) => (
                    <Checkbox.Root
                        key={keyword}
                        checked={crossedKeywords.includes(keyword)}
                        onChange={() => toggleKeywordCrossing(keyword)}
                    >
                        <Checkbox.HiddenInput />
                        <Checkbox.Label style={{ textDecoration: crossedKeywords.includes(keyword) ? "line-through" : "none" }}>
                            {keyword}{index === allKeywords.length - 1?"":","}
                        </Checkbox.Label>
                    </Checkbox.Root>
                ))}
            </Flex>
                <Field.Root orientation="horizontal">
                    <Field.Label>Add keyword</Field.Label>
                    <Group attached w="full" maxW="sm">
                        <Input flex="1" placeholder="New keyword" value={newKeyword} onChange={(e) => setNewKeyword(e.target.value)} />
                        <Button bg="bg.subtle" variant="outline" onClick={addKeyword}>
                            Add
                        </Button>
                    </Group>
                </Field.Root>
        </Stack>
    )
}