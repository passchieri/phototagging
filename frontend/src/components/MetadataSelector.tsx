import { DatePicker, Field, Flex, FlexProps, Input, Portal, Slider, DateValue, Box, SliderThumb } from "@chakra-ui/react";
import { useMetadata } from "./MetadataProvider";
import { LuCalendar } from "react-icons/lu"
import { parseDate } from "@chakra-ui/react";
import { useState } from "react";


export function MetadataSelector(props: FlexProps) {
    const { fileFilter, setFileFilter, keywordFilter, setKeywordFilter, setDateFilter, metadataSet } = useMetadata();

    function updateDateRange({ value }: { value: number[] }) {
        if (value.length < 2 || !minDate || !maxDate) return;
        const duration = (maxDate.toDate("UTC").getTime() - minDate.toDate("UTC").getTime()) / (24 * 60 * 60 * 1000);
        const first = minDate.add({ days: Math.floor(value[0] / 100 * duration) });
        const last = minDate.add({ days: Math.ceil(value[1] / 100 * duration) });
        console.log(first, last);
        setDateRange({first,last});
        setDateFilter({ first, last })

    }

    const initTxt = Object.values(metadataSet)[0]?.create_date || "2026-01-01";
    
    const initDate = parseDate(initTxt.slice(0, 10));
    const minTxt = Object.values(metadataSet).reduce((min, entry) =>
        entry.create_date < min ? entry.create_date : min
        , initTxt);
    const minDate = (minTxt ? parseDate(minTxt.slice(0, 10)) : undefined)
    const maxTxt = Object.values(metadataSet).reduce((max, entry) =>
        entry.create_date > max ? entry.create_date : max
        , initTxt);
    const maxDate = (maxTxt ? parseDate(maxTxt.slice(0, 10)) : undefined)

    const [dateRange, setDateRange] = useState<{ first: DateValue, last: DateValue }>({ first: minDate || initDate, last: maxDate || initDate });
    return (
        <Flex {...props} direction="horizontal" flexFlow="initial" gap={3} mt={3} mb={3}>
            <Field.Root orientation="vertical" width={300}>
                <Field.Label>File</Field.Label>
                <Input padding={2} variant="outline" flex="0" placeholder="File name" value={fileFilter} onChange={(e) => setFileFilter(e.target.value)} />
            </Field.Root>
            <Field.Root orientation="vertical" width={300}>
                <Field.Label>Keyword</Field.Label>
                <Input padding={2} variant="outline" flex="0" placeholder="Keyword" value={keywordFilter} onChange={(e) => setKeywordFilter(e.target.value)} />
            </Field.Root>
            <DatePicker.Root ml={3} disabled={true} format={(date)=>date.toString() } selectionMode="range" width={300} min={minDate} max={maxDate} value={[dateRange.first, dateRange.last]} onValueChange={(e) => setDateFilter({ first: e.value?.[0], last: e.value?.[1] })}>
                <DatePicker.Label>Date range</DatePicker.Label>
                <DatePicker.Control>
                    <DatePicker.Input index={0} />
                    <DatePicker.Input index={1} />
                    <DatePicker.IndicatorGroup>
                    </DatePicker.IndicatorGroup>
                </DatePicker.Control>
            <Slider.Root width={300} defaultValue={[0, 100]}
                thumbCollisionBehavior="swap"
                onValueChange={updateDateRange}>
                <Slider.Control>
                    <Slider.Track>
                        <Slider.Range />
                    </Slider.Track>
                    <Slider.Thumbs/>
                </Slider.Control>
            </Slider.Root>
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

