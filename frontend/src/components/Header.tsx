import { Heading, Flex, Stack } from "@chakra-ui/react";
import { ImageSelector } from "./ImageSelector";
import Pagination from "./Pagination";

const Header = () => {
  return (
    <Stack
      direction="column"
      bg="gray.400"
      padding={5}
    >
      <Flex
        as="nav"
        align="left"
        justify="space-between"
        wrap="wrap"
        padding="1rem"
        direction="column"
        gap={5}
      >
        <Heading as="h1">Images</Heading>
      </Flex>
    </Stack>
  );
};

export default Header;
