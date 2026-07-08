import { createContext, ReactNode, useState, useEffect, useContext } from "react";
import { Metadata, PhotoTaggingClient } from "../api";
import { DateValue, parseDate } from "@chakra-ui/react";

const DEFAULT_URL = "http://localhost:8000";
const DEFAULT_PAGING = { page: 1, size: 12, total: 1 }
export interface PagingData {
    page: number;
    size: number;
    total: number;
}
interface MetadataProviderValue {
    url: string;
    fileFilter: string;
    setFileFilter: (filter: string) => void;
    keywordFilter: string;
    setKeywordFilter: (filter: string) => void;
    dateFilter: { first: DateValue | undefined, last: DateValue | undefined };
    setDateFilter: ({ first, last }: { first: DateValue | undefined, last: DateValue | undefined }) => void;
    metadataSet:Metadata[];
    filteredMetadataSet: Metadata[];
    pagingData: PagingData;
    setPagingData: (pagingData: PagingData) => void;
}
const MetadataProviderContext = createContext<MetadataProviderValue>({
    fileFilter: "",
    setFileFilter: () => { },
    keywordFilter: "",
    setKeywordFilter: () => { },
    dateFilter: { first: undefined, last: undefined },
    setDateFilter: () => { },
    metadataSet:[],
    filteredMetadataSet: [],
    pagingData: DEFAULT_PAGING,
    setPagingData: () => { },
    url: DEFAULT_URL
});

export function MetadataProvider({ children }: { children: ReactNode; }) {
    const [fileFilter, setFileFilter] = useState<string>("");
    const [keywordFilter, setKeywordFilter] = useState<string>("");
    const [dateFilter, setDateFilter] = useState<{ first: DateValue | undefined, last: DateValue | undefined }>({ first: undefined, last: undefined })
    const [metadataSet, setMetadataSet] = useState<Metadata[]>([]);
    const [filteredMetadataSet, setFilteredMetadataSet] = useState<Metadata[]>([]);
    const [pagingData, setPagingData] = useState<PagingData>(DEFAULT_PAGING);
    const url = DEFAULT_URL;


    const client = new PhotoTaggingClient({ "BASE": url })

    const fetchImages = async () => {
        const metadata = await client.metadata.getMetadatas();
        const sortedMetadata = [...metadata].sort((a, b) => {
            return new Date(b.create_date).getTime() - new Date(a.create_date).getTime();
        });
        setMetadataSet(sortedMetadata);
    };
    useEffect(() => {
        fetchImages();
    }, []);


    useEffect(() => {
        const data = metadataSet
            .filter(md => {
                if (fileFilter === "") return true;
                return (md.filename.indexOf(fileFilter) >= 0);
            })
            .filter(md => {
                if (keywordFilter === "") return true;

                const kwFilters = keywordFilter
                    .split(",")
                    .map(k => k.trim().toLowerCase())
                    .filter(k => k.length > 0);

                return kwFilters.every(f => md.keywords.some(kw => kw.toLowerCase().includes(f))
                );
            })
            .filter(md => {
                if (dateFilter.first === undefined) return true;
                return (parseDate(md.create_date.slice(0, 10)) >= dateFilter.first)
            })
            .filter(md => {
                if (dateFilter.last === undefined) return true;
                return (parseDate(md.create_date.slice(0, 10)) <= dateFilter.last);
            })
            ;
        if (pagingData.page > pagingData.total) {
            setPagingData({ ...pagingData, page: 1 });
            return; //This will make us come back with an existing page
        }

        const start = (pagingData.page - 1) * pagingData.size;
        const end = start + pagingData.size;
        setFilteredMetadataSet(data.slice(start, end));
        const totalPages = Math.max(1, Math.ceil((data.length) / pagingData.size));
        const page = Math.min(totalPages, pagingData.page);
        if ((totalPages != pagingData.total) || (page != pagingData.page)) {
            setPagingData({ ...pagingData, total: totalPages, page: Math.min(totalPages, pagingData.page) })
        }
    }, [metadataSet, fileFilter, keywordFilter, pagingData, dateFilter]);



    return (
        <MetadataProviderContext.Provider value={{
            url,
            fileFilter,
            setFileFilter,
            keywordFilter,
            setKeywordFilter,
            dateFilter,
            setDateFilter,
            metadataSet,
            filteredMetadataSet,
            pagingData,
            setPagingData,
        }}>
            {children}
        </MetadataProviderContext.Provider>
    );
}

export function useMetadata() {
    const ctx = useContext(MetadataProviderContext);
    if (!ctx) {
        throw new Error("useMetadata must be used inside <MetadataProvider>");
    }
    return ctx;
}
