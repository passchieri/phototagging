import { createContext, ReactNode, useState, useEffect, useContext } from "react";
import { ImageMetadata } from "./interfaces";

interface ImageProviderValue {
    url: string;
    fileFilter: string;
    setFileFilter: (filter: string) => void;
    keywordFilter: string;
    setKeywordFilter: (filter: string) => void;
    filteredMetadataSet: ImageMetadata[];
    setFilteredMetadataSet: (images: ImageMetadata[]) => void;
    pagingData: { page: number; size: number; };
    setPagingData: ({ page, size }: { page: number; size: number; }) => void;
    imageCount: number;
    setImageCount: (count: number) => void;
}
const ImageProviderContext = createContext<ImageProviderValue>({
    fileFilter: "",
    setFileFilter: () => { },
    keywordFilter: "",
    setKeywordFilter: () => { },
    filteredMetadataSet: [],
    setFilteredMetadataSet: () => { },
    pagingData: { page: 0, size: 9 },
    setPagingData: () => { },
    imageCount: 0,
    setImageCount: () => { },
    url: "http://localhost:8000/"
});

export function ImageProvider({ children }: { children: ReactNode; }) {
    const [fileFilter, setFileFilter] = useState<string>("");
    const [keywordFilter, setKeywordFilter] = useState<string>("");
    const [metadataSet, setMetadataSet] = useState<ImageMetadata[]>([]);
    const [filteredMetadataSet, setFilteredMetadataSet] = useState<ImageMetadata[]>([]);
    const [pagingData, setPagingData] = useState({ page: 1, size: 9 });
    const [imageCount, setImageCount] = useState<number>(0);
    const url = "http://localhost:8000/";

    const fetchImages = async () => {
        const response = await fetch(`${url}images`);
        const resp = await response.json();
        setMetadataSet(resp.data);
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
            });
        const totalPages = Math.ceil(data.length / pagingData.size);
        if (pagingData.page > totalPages && totalPages > 0) {
            setPagingData({ ...pagingData, page: 1 });
            return; //This will make us come back with an existing page
        }

        const start = (pagingData.page - 1) * pagingData.size;
        const end = start + pagingData.size;
        setFilteredMetadataSet(data.slice(start, end));
        setImageCount(data.length);
    }, [metadataSet, fileFilter, keywordFilter, pagingData]);



    return (
        <ImageProviderContext.Provider value={{
            url,
            fileFilter,
            setFileFilter,
            keywordFilter,
            setKeywordFilter,
            filteredMetadataSet,
            setFilteredMetadataSet,
            pagingData,
            setPagingData,
            imageCount,
            setImageCount
        }}>
            {children}
        </ImageProviderContext.Provider>
    );
}

export function useImages() {
    const ctx = useContext(ImageProviderContext);
    if (!ctx) {
        throw new Error("useImageSelector must be used inside <ImageSelectorProvider>");
    }
    return ctx;
}
