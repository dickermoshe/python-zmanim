from datetime import datetime, timedelta, date
from datetime import datetime, timedelta, date
from typing import Optional

from zmanim.astronomical_calendar import AstronomicalCalendar
from zmanim.hebrew_calendar.jewish_calendar import JewishCalendar
from zmanim.util.astronomical_calculations import AstronomicalCalculations
from zmanim.util.geo_location import GeoLocation


class ZmanimCalendar(AstronomicalCalendar):
	"""
 	The ZmanimCalendar is a specialized calendar that can calculate sunrise, sunset and Jewish zmanim.
    (religious times) for prayers and other Jewish religious duties. This class contains the main functionality of the
    Zmanim library.
 	"""
    def __init__(
        self,
        candle_lighting_offset: int = 18,
        geo_location: Optional[GeoLocation] = None,
        date: Optional[date] = None,
        calculator: Optional[AstronomicalCalculations] = None,
        *args,
        **kwargs,
    ):
        """The ZmanimCalendar is a specialized calendar that can calculate sunrise, sunset and Jewish zmanim.
        (religious times) for prayers and other Jewish religious duties. This class contains the main functionality of the
        Zmanim library.


        Args:
            candle_lighting_offset (Optional[int], optional): How many minutes before sunset candle lighting time defaults to. Defaults to 18.
            geo_location (Optional[GeoLocation], optional): The location to calculate zmanim for. Defaults to `GeoLocation.GMT()`.
            date (Optional[date], optional): Date to calculate zmanim for. Defaults to `datetime.today()`.
            calculator (Optional[AstronomicalCalculations], optional): Zmanim Calculator Class. Defaults to `NOAACalculator`.
        """
        super(ZmanimCalendar, self).__init__(
            date=date, geo_location=geo_location, calculator=calculator
        )
        self.candle_lighting_offset = candle_lighting_offset
        self.use_elevation = False

    def __repr__(self):
        return (
            "%s(candle_lighting_offset=%r, geo_location=%r, date=%r, calculator=%r)"
            % (
                self.__module__ + "." + self.__class__.__qualname__,
                self.candle_lighting_offset,
                self.geo_location,
                self.date,
                self.astronomical_calculator,
            )
        )

    def elevation_adjusted_sunrise(self) -> Optional[datetime]:
        """
        This method will return sea level sunrise if `self.use_elevation` is false (the
        default), or elevation adjusted sunrise if it is true. 
        Will return `None` if there is no sunrise on this day.
        """
        
        return self.sunrise() if self.use_elevation else self.sea_level_sunrise()

    def hanetz(self) -> Optional[datetime]:
        """
        This method returns Hanetz (sunrise). It's a wrapper for `self.elevation_adjusted_sunrise()`.
        Will return `None` if there is no sunrise on this day.
        """

        return self.elevation_adjusted_sunrise()

    def elevation_adjusted_sunset(self) -> Optional[datetime]:
        """
        This method will return sea level sunset if `self.use_elevation` is false (the
        default), or elevation adjusted sunset if it is true. 
        Will return `None` if there is no sunset on this day.
        """

        return self.sunset() if self.use_elevation else self.sea_level_sunset()

    def shkia(self) -> Optional[datetime]:
        """
        This method returns Shkia (sunset). It's a wrapper for `self.elevation_adjusted_sunset()`.
        Will return `None` if there is no sunset on this day.
        """

        return self.elevation_adjusted_sunset()

    def tzais(self, opts: dict = {"degrees": 8.5}) -> Optional[datetime]:
        """
        A method that returns tzais (nightfall) when the sun is 8.5 degrees below the
        geometric horizon (90 degrees) after sunset.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        
        degrees, offset, zmanis_offset = self._extract_degrees_offset(opts)
        sunset_for_degrees = (
            self.elevation_adjusted_sunset()
            if degrees == 0
            else self.sunset_offset_by_degrees(self.GEOMETRIC_ZENITH + degrees)
        )
        if zmanis_offset != 0:
            return self._offset_by_minutes_zmanis(sunset_for_degrees, zmanis_offset)
        else:
            return self._offset_by_minutes(sunset_for_degrees, offset)

    def tzais_72(self) -> Optional[datetime]:
        """
        This method returns the tzais (nightfall) based on the opinion of Rabbeinu Tam that
        tzais hakochavim is calculated as 72 minutes after sunset.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        
        return self.tzais({"offset": 72})

    def alos(self, opts: dict = {"degrees": 16.1}) -> Optional[datetime]:
        """
        Returns alos (dawn) based on the time when the sun is 16.1 degrees below the
	    eastern geometric horizon before sunrise.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        
        degrees, offset, zmanis_offset = self._extract_degrees_offset(opts)
        sunrise_for_degrees = (
            self.elevation_adjusted_sunrise()
            if degrees == 0
            else self.sunrise_offset_by_degrees(self.GEOMETRIC_ZENITH + degrees)
        )
        if zmanis_offset != 0:
            return self._offset_by_minutes_zmanis(sunrise_for_degrees, -zmanis_offset)
        else:
            return self._offset_by_minutes(sunrise_for_degrees, -offset)

    def alos_72(self) -> Optional[datetime]:
        """
        Method to return alos (dawn) calculated using 72 minutes before sunrise.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        
        return self.alos({"offset": 72})

    def chatzos(self) -> Optional[datetime]:
        """
        This method returns chatzos (midday) following most opinions that chatzos is the midpoint
	    between sunrise and sunset.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        return self.sun_transit()

    def candle_lighting(self) -> Optional[datetime]:
        """
        A method to return candle lighting time, calculated as `candle_lighting_offset` minutes before
	    sunset. This will return the time for any day of the week, since it can be
	    used to calculate candle lighting time for Yom Tov (mid-week holidays) as well.
        Will return `None` if there is no sunset or sunrise on this day.
        """

        return self._offset_by_minutes(
            self.sea_level_sunset(), - self.candle_lighting_offset
        )

    def sof_zman_shma(
        self, day_start: datetime, day_end: datetime
    ) -> Optional[datetime]:
        """
        A generic method for calculating the latest zman krias shema (time to recite shema in the morning)
	    that is 3 shaos zmaniyos (temporal hours) after the start of the day, calculated using the start and
	    end of the day passed to this method.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        
        return self._shaos_into_day(day_start, day_end, 3)

    def sof_zman_shma_gra(self) -> Optional[datetime]:
        """
        This method returns the latest zman krias shema (time to recite shema in the morning) that is 3
	    shaos zmaniyos (solar hours) after sunrise.
        Will return `None` if there is no sunset or sunrise on this day.
        """

        elevation_adjusted_sunrise = self.elevation_adjusted_sunrise()
        elevation_adjusted_sunset = self.elevation_adjusted_sunset()
        if elevation_adjusted_sunrise is None or elevation_adjusted_sunset is None:
            return None
        return self.sof_zman_shma(elevation_adjusted_sunrise, elevation_adjusted_sunset)

    def sof_zman_shma_mga(self) -> Optional[datetime]:
        """
        This method returns the latest zman krias shema (time to recite shema in the morning) that is 3
	    shaos zmaniyos (solar hours) after `alos_72`, according to the opinion that the day is calculated
	    from 72 minutes before sunrise to 72 minutes after sunset.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        alos_72 = self.alos_72()
        tzais_72 = self.tzais_72()
        if alos_72 is None or tzais_72 is None:
            return None
        return self.sof_zman_shma(alos_72, tzais_72)

    def sof_zman_tfila(
        self, day_start: Optional[datetime], day_end: Optional[datetime]
    ) -> Optional[datetime]:
        """
        A generic method for calculating the latest zman tfilah (time to recite the morning prayers)
	    that is 4 shaos zmaniyos (temporal hours) after the start of the day, calculated using the start and
	    end of the day passed to this method.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        return self._shaos_into_day(day_start, day_end, 4)

    def sof_zman_tfila_gra(self) -> Optional[datetime]:
        """
        This method returns the latest zman tfilah (time to recite the morning prayers) that is 4
	    shaos zmaniyos (solar hours) after sunrise.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        return self.sof_zman_tfila(
            self.elevation_adjusted_sunrise(), self.elevation_adjusted_sunset()
        )

    def sof_zman_tfila_mga(self) -> Optional[datetime]:
        """
        This method returns the latest zman tfilah (time to recite the morning prayers) that is 4
	    shaos zmaniyos (solar hours) after `alos_72`, according to the opinion that the day is calculated
	    from 72 minutes before sunrise to 72 minutes after sunset.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        return self.sof_zman_tfila(self.alos_72(), self.tzais_72())

    def mincha_gedola(
        self, day_start: Optional[datetime] = None, day_end: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        A generic method for calculating the latest mincha gedola (the earliest time to recite the mincha prayers)
	    that is 6.5 shaos zmaniyos (temporal hours) after the start of the day, calculated using the start and end
	    of the day passed to this method.
        `day_start` and `day_end` are optional, and will default to the elevation adjusted sunrise and sunset.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        if day_start is None:
            day_start = self.elevation_adjusted_sunrise()
        if day_end is None:
            day_end = self.elevation_adjusted_sunset()

        return self._shaos_into_day(day_start, day_end, 6.5)

    def mincha_ketana(
        self, day_start: Optional[datetime] = None, day_end: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        A generic method for calculating mincha ketana, (the preferred time to recite the mincha prayers in
	    the opinion that is 9.5 shaos zmaniyos (temporal hours) after the start of the day, calculated using the start and end
	    of the day passed to this method.
        `day_start` and `day_end` are optional, and will default to the elevation adjusted sunrise and sunset.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        if day_start is None:
            day_start = self.elevation_adjusted_sunrise()
        if day_end is None:
            day_end = self.elevation_adjusted_sunset()

        return self._shaos_into_day(day_start, day_end, 9.5)

    def plag_hamincha(
        self, day_start: Optional[datetime] = None, day_end: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        A generic method for calculating plag hamincha (the earliest time that Shabbos can be started) that is
	    10.75 hours after the start of the day, (or 1.25 hours before the end of the day) based on the start and end of
	    the day passed to the method.
        `day_start` and `day_end` are optional, and will default to the elevation adjusted sunrise and sunset.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        if day_start is None:
            day_start = self.elevation_adjusted_sunrise()
        if day_end is None:
            day_end = self.elevation_adjusted_sunset()

        return self._shaos_into_day(day_start, day_end, 10.75)

    def shaah_zmanis(
        self, day_start: Optional[datetime], day_end: Optional[datetime]
    ) -> Optional[float]:
        """
        A generic utility method for calculating any shaah zmanis (temporal hour) based zman with the
	    day defined as the start and end of day (or night) and the number of shaahos zmaniyos passed to the
	    method.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        return self.temporal_hour(day_start, day_end)

    def shaah_zmanis_gra(self) -> Optional[float]:
        """
        A generic utility method for calculating any shaah zmanis (temporal hour) occording to the opinion
        that the day is calculated from sunrise to sunset.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        return self.shaah_zmanis(
            self.elevation_adjusted_sunrise(), self.elevation_adjusted_sunset()
        )

    def shaah_zmanis_mga(self) -> Optional[float]:
        """
        A generic utility method for calculating any shaah zmanis (temporal hour) occording to the opinion
        that the day is calculated from 72 minutes before sunrise to 72 minutes after sunset.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        
        return self.shaah_zmanis(self.alos_72(), self.tzais_72())

    def shaah_zmanis_by_degrees_and_offset(
        self, degrees: float, offset: float
    ) -> Optional[float]:
        """
        A generic utility method for calculating any shaah zmanis (temporal hour) occording to the opinion
        that the day is calculated from sunrise to sunset.
        You can pass degrees and offset to this method to ajust how the sunset and sunrise are calculated.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        
        opts = {"degrees": degrees, "offset": offset}
        return self.shaah_zmanis(self.alos(opts), self.tzais(opts))

    def is_assur_bemelacha(
        self, current_time: datetime, tzais=None, in_israel: Optional[bool] = False
    ) -> Optional[bool]:
        """
        This is a utility method to determine if the current Date (datetime) passed in has a melacha (work) prohibition.
	    Since there are many opinions on the time of tzais, the tzais for the current day has to be passed to this
	    class. Sunset is the classes current day's sunset that observes the
	    The `JewishCalendar.in_israel` will be set by the in_israel parameter.
        Will return `None` if there is no sunset or sunrise on this day.
        """
        if tzais is None:
            tzais_time = self.tzais()
        elif isinstance(tzais, dict):
            tzais_time = self.tzais(tzais)
        else:
            tzais_time = tzais

        if tzais_time is None:
            return None

        elevation_adjusted_sunset = self.elevation_adjusted_sunset()
        if elevation_adjusted_sunset is None:
            return None

        jewish_calendar = JewishCalendar(current_time.date())
        jewish_calendar.in_israel = in_israel
        return (
            current_time <= tzais_time and jewish_calendar.is_assur_bemelacha()
        ) or (
            current_time >= elevation_adjusted_sunset
            and jewish_calendar.is_tomorrow_assur_bemelacha()
        )

    def _shaos_into_day(
        self, day_start: Optional[datetime], day_end: Optional[datetime], shaos: float
    ) -> Optional[datetime]:
        shaah_zmanis = self.temporal_hour(day_start, day_end)
        if shaah_zmanis is None:
            return None
        return self._offset_by_minutes(
            day_start, (shaah_zmanis / self.MINUTE_MILLIS) * shaos
        )

    def _extract_degrees_offset(self, opts: dict) -> tuple:
        degrees = opts["degrees"] if "degrees" in opts else 0
        offset = opts["offset"] if "offset" in opts else 0
        zmanis_offset = opts["zmanis_offset"] if "zmanis_offset" in opts else 0
        return degrees, offset, zmanis_offset

    def _offset_by_minutes(
        self, time: Optional[datetime], minutes: float
    ) -> Optional[datetime]:
        if time is None:
            return None
        return time + timedelta(minutes=minutes)

    def _offset_by_minutes_zmanis(
        self, time: Optional[datetime], minutes: float
    ) -> Optional[datetime]:
        if time is None:
            return None
        shaah_zmanis_gra = self.shaah_zmanis_gra()
        if shaah_zmanis_gra is None:
            return None
        shaah_zmanis_skew = shaah_zmanis_gra / self.HOUR_MILLIS
        return time + timedelta(minutes=minutes * shaah_zmanis_skew)
