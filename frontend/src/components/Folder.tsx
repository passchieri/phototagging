import { Box, BoxProps, HStack, Text } from "@chakra-ui/react";
import { useState } from "react";

import { LuChevronDown, LuChevronRight, LuFile } from "react-icons/lu"
export type FolderData = {
    name: String;
    isFolder?: Boolean;
    children?: FolderData[]
}

type Props = BoxProps & {
    data: FolderData[];
};

export function Folder({ data, ...boxProps }: Props) {

    return (
        <Box {...boxProps}>
            {data.map((item) => (
                <FolderItem item={item} />
            ))}
        </Box>
    );

}

function FolderItem({ item }: { item: FolderData }) {
    const [open, setOpen] = useState(false);

    const toggle = () => {
        if (item.isFolder) setOpen(!open);
    };

    return (
        <Box ml={4}>
            <HStack onClick={toggle} cursor={item.isFolder ? "pointer" : "default"}>
                {item.isFolder ? (
                    open ? <LuChevronDown /> : <LuChevronRight />
                ) : (
                    <LuFile />
                )}

                <Text fontWeight={item.isFolder ? "bold" : "normal"}>
                    {item.name}
                </Text>
            </HStack>

            {item.isFolder && open && item.children && (
                <Folder data={item.children} ml={4} />
            )}
        </Box>
    );
}
