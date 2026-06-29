import { Button, Group, GroupProps } from "@chakra-ui/react";
import { useImages } from "./ImageProvider";

const maxButtons = 9;

function createButton(p: number, page: number, size: number, onPageChange: ({ page, size }: {
  page: number;
  size: number;
}) => void) {
  return (
    <Button
      key={p}
      variant={p === page ? "solid" : "outline"}
      onClick={() => onPageChange({ page: p, size })}
    >
      {p}
    </Button>
  )

}
export default function Pagination(props:GroupProps) {
  const { pagingData, imageCount, setPagingData } = useImages();
  const totalPages = Math.ceil(imageCount / pagingData.size);


  let start = 1;
  let end = totalPages;
  if (totalPages > maxButtons) {
    if (pagingData.page < maxButtons / 2) {
      start = 1;
      end = start + maxButtons - 1;
    } else if (pagingData.page > (totalPages - maxButtons / 2)) {
      end = totalPages;
      start = totalPages - maxButtons + 1;
    } else {
      start = Math.ceil(pagingData.page - maxButtons / 2);
      end = start + maxButtons - 1;
    }
  }
  const pages = Array.from({ length: end - start + 1 }, (_, i) => i + start);
  return (
    <Group attached {...props} >
      <Button
        key="first"
        aria-label="Previous"
        disabled={pagingData.page === 1}
        onClick={() => setPagingData({ page: 1, size: pagingData.size })}
      >
        &lt;&lt;
      </Button>
      <Button
        key="previous"
        aria-label="Previous"
        disabled={pagingData.page === 1}
        onClick={() => setPagingData({ page: pagingData.page - 1, size: pagingData.size })}
      >
        &lt;
      </Button>
      {pages.map((p) => createButton(p, pagingData.page, pagingData.size, setPagingData))}
      <Button
        key="next"
        aria-label="Next"
        disabled={pagingData.page === totalPages}
        onClick={() => setPagingData({ page: pagingData.page + 1, size: pagingData.size })}
      >
        &gt;
      </Button>
      <Button
        key="last"
        aria-label="Next"
        disabled={pagingData.page === totalPages}
        onClick={() => setPagingData({ page: totalPages, size: pagingData.size })}
      >
        &gt;&gt;
      </Button>
    </Group>
  );
}
