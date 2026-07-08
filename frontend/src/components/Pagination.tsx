import { Button, Group, GroupProps } from "@chakra-ui/react";
import { useMetadata } from "./MetadataProvider";

const maxButtons = 9;

export default function Pagination(props: GroupProps) {
  const { pagingData, setPagingData } = useMetadata();

  function createButton(p: number) {
    return (
      <Button
        key={p}
        variant={p === pagingData.page ? "solid" : "outline"}
        onClick={() => setPagingData({ ...pagingData, page: p })}
      >
        {p}
      </Button>
    )
  }

  let start = 1;
  let end = pagingData.total;
  if (pagingData.total > maxButtons) {
    if (pagingData.page < maxButtons / 2) {
      start = 1;
      end = start + maxButtons - 1;
    } else if (pagingData.page > (pagingData.total - maxButtons / 2)) {
      end = pagingData.total;
      start = pagingData.total - maxButtons + 1;
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
        aria-label="First"
        disabled={pagingData.page === 1}
        onClick={() => setPagingData({ ...pagingData, page: 1 })}
      >
        &lt;&lt;
      </Button>
      <Button
        key="previous"
        aria-label="Previous"
        disabled={pagingData.page === 1}
        onClick={() => setPagingData({ ...pagingData, page: pagingData.page - 1 })}
      >
        &lt;
      </Button>
      {pages.map((p) => createButton(p))}
      <Button
        key="next"
        aria-label="Next"
        disabled={pagingData.page === pagingData.total}
        onClick={() => setPagingData({ ...pagingData, page: pagingData.page + 1 })}
      >
        &gt;
      </Button>
      <Button
        key="last"
        aria-label="Last"
        disabled={pagingData.page === pagingData.total}
        onClick={() => setPagingData({ ...pagingData, page: pagingData.total })}
      >
        &gt;&gt;
      </Button>
    </Group>
  );
}
