import { Box, Flex } from '@chakra-ui/react'
import Header from "./components/Header";
import Images from './components/Images';
import { ImageProvider } from "./components/ImageProvider";
import Pagination from './components/Pagination';
import { ImageSelector } from './components/ImageSelector';


function App() {

  return (
    <ImageProvider>
      <Flex direction="column" height="100vh">

        {/* Header: natural height */}
        <Box flex="0 0 auto">
          <Header />
        </Box>
        <Box flex="0 0 auto">
          <ImageSelector m={5} />
        </Box>

        {/* Body: fills remainder, scrolls if needed */}
        <Box flex="1 1 auto" overflowY="auto">
          <Images />
        </Box>
        <Box flex="0 0 auto">
          <Pagination m={5} />
        </Box>

      </Flex>


    </ImageProvider>
  )
}

export default App;