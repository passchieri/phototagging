import { Box, Flex } from '@chakra-ui/react'
import Header from "./components/Header";
import { MetadataProvider } from "./components/MetadataProvider";
import MetadataPage from './components/MetadataPage';
import { FolderData, Folder } from './components/Folder';


const data: FolderData[] = [
  {
    name: "top", isFolder: true, children: [
      { name: "a", isFolder: true, children: [
        {name: "childa",isFolder:false}
      ] },
      { name: "b", isFolder: true, children: [] },
      { name: "file", isFolder: false },
      { name: "file 2", isFolder: false }
    ]
  }
]

function App() {

  return (
    <MetadataProvider>
      <Flex flex="1 1 auto" direction="column" height="100dvh">
        {/* Header: natural height */}
        <Box flex="0 0 auto">
          <Header />
        </Box>
        <Flex direction="row" maxHeight="100%">
          <Folder data={data} minW="200px" />
          <Box flex="1 1 auto" maxHeight="100%" overflowY="auto">
            <MetadataPage />
          </Box>
        </Flex>
      </Flex>

    </MetadataProvider>
  )
}

export default App;