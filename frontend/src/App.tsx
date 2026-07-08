import { Box, Flex } from '@chakra-ui/react'
import Header from "./components/Header";
import { MetadataProvider } from "./components/MetadataProvider";
import MetadataPage from './components/MetadataPage';

function App() {

  return (
    <MetadataProvider>
      <Flex direction="column" height="100dvh">
        {/* Header: natural height */}
        <Box flex="0 0 auto">
          <Header />
        </Box>
        <Box flex="1 1 auto" maxHeight="100%" overflowY="auto">
          <MetadataPage />
        </Box>
      </Flex>


    </MetadataProvider>
  )
}

export default App;