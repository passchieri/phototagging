import { DatePicker, Field, Flex, FlexProps, Input, Portal } from "@chakra-ui/react";
import { useMetadata } from "./MetadataProvider";
import { LuCalendar } from "react-icons/lu"
import { DateValue, parseDate } from "@chakra-ui/react";


export function MetadataSelector(props: FlexProps) {
    const { fileFilter, setFileFilter, keywordFilter, setKeywordFilter, dateFilter, setDateFilter, metadataSet } = useMetadata();

    const minTxt = metadataSet.reduce((min, entry) =>
        entry.create_date < min ? entry.create_date : min
        , metadataSet[0]?.create_date);
    const minDate = (minTxt ? parseDate(minTxt.slice(0, 10)):undefined)
    const maxTxt = metadataSet.reduce((max, entry) =>
        entry.create_date > max ? entry.create_date : max
        , metadataSet[0]?.create_date);
    const maxDate=(maxTxt? parseDate(maxTxt.slice(0,10)):undefined)
    console.log(minTxt?.slice(0,10), maxTxt?.slice(0,10));

    return (
        <Flex {...props} direction="horizontal" flexFlow="initial" gap={3} mt={3} mb={3}>
            <Field.Root orientation="vertical" width={300}>
                <Field.Label>File</Field.Label>
                <Input padding={2} variant="outline" flex="1" placeholder="File name" value={fileFilter} onChange={(e) => setFileFilter(e.target.value)} />
            </Field.Root>
            <Field.Root orientation="vertical" width={300}>
                <Field.Label>Keyword</Field.Label>
                <Input padding={2} variant="outline" flex="1" placeholder="Keyword" value={keywordFilter} onChange={(e) => setKeywordFilter(e.target.value)} />
            </Field.Root>
            <DatePicker.Root selectionMode="range" width={300} min={minDate} max={maxDate} value={dateFilter.first && dateFilter.last ? [dateFilter.first, dateFilter.last] : undefined} onValueChange={(e) => setDateFilter({ first: e.value?.[0], last: e.value?.[1] })}>
                <DatePicker.Label>Select range</DatePicker.Label>
                <DatePicker.Control>
                    <DatePicker.Input index={0} />
                    <DatePicker.Input index={1} />
                    <DatePicker.IndicatorGroup>
                        <DatePicker.Trigger>
                            <LuCalendar />
                        </DatePicker.Trigger>
                    </DatePicker.IndicatorGroup>
                </DatePicker.Control>
                <Portal>
                    <DatePicker.Positioner>
                        <DatePicker.Content>
                            <DatePicker.View view="day">
                                <DatePicker.Header />
                                <DatePicker.DayTable />
                            </DatePicker.View>
                            <DatePicker.View view="month">
                                <DatePicker.Header />
                                <DatePicker.MonthTable />
                            </DatePicker.View>
                            <DatePicker.View view="year">
                                <DatePicker.Header />
                                <DatePicker.YearTable />
                            </DatePicker.View>
                        </DatePicker.Content>
                    </DatePicker.Positioner>
                </Portal>
            </DatePicker.Root>
        </Flex>
    )
}

