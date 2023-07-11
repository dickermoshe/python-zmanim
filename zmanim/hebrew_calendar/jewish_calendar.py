from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from dateutil import tz

from zmanim.hebrew_calendar.jewish_date import JewishDate
from zmanim.hebrew_calendar.constants import SIGNIFICANT_SHABBOS,SIGNIFICANT_DAYS

from zmanim.util.geo_location import GeoLocation

class JewishCalendar(JewishDate):
    SIGNIFICANT_SHABBOS = SIGNIFICANT_SHABBOS
    SIGNIFICANT_DAYS = SIGNIFICANT_DAYS

    def __init__(self, *args, **kwargs):
        """
        Initializes a JewishDate object.  
        You can pass either a `datetime.date` object, a Jewish year, month, and day, or a molad.
        If no arguments are passed, the date will be set to the current system date.
        Use the `in_israel` keyword argument to set the calendar to Israel. This will affect the
        calculation of holidays and parshios. If the `in_israel` keyword argument is not passed,
        the calendar will default to Diaspora mode.
        
        Examples:
            ```
            # Using Current Date
            >>> JewishDate()        
            <zmanim.hebrew_calendar.jewish_date.JewishDate gregorian_date=datetime.date(2023, 7, 10) ... >
            
            # Using a `datetime.date` object
            >>> from datetime import date
            >>> d = date(2021,1,1) 
            >>> JewishDate(d)        
            <zmanim.hebrew_calendar.jewish_date.JewishDate gregorian_date=datetime.date(2021, 1, 1) ... >
            
            # Using the Jewish Year, Month, and Day
            >>> JewishDate(5776,1,1) 
            <zmanim.hebrew_calendar.jewish_date.JewishDate gregorian_date=datetime.date(2016, 4, 9), ... >
            
            # Using the Molad
            >>> JewishDate(54692515673) 
            <zmanim.hebrew_calendar.jewish_date.JewishDate gregorian_date=datetime.date(2017, 10, 20) ...>
            ```
        """
        in_israel = None
        if 'in_israel' in kwargs:
            in_israel = kwargs.pop('in_israel')
        if len(args) == 4:
            super(JewishCalendar, self).__init__(*args[:3], **kwargs)
            in_israel = args[3]
        else:
            super(JewishCalendar, self).__init__(*args, **kwargs)
        self.in_israel = False if in_israel is None else in_israel
        self.use_modern_holidays = False

    def __repr__(self):
        return "<%s in_israel=%r, gregorian_date=%r, jewish_date=%r, day_of_week=%r, molad_hours=%r, molad_minutes=%r, molad_chalakim=%r>" % \
               (self.__module__ + "." + self.__class__.__qualname__, self.in_israel, self.gregorian_date,
                self.jewish_date, self.day_of_week, self.molad_hours, self.molad_minutes, self.molad_chalakim)

    def significant_day(self) -> Optional[str]:
        return getattr(self, f'_{self.jewish_month_name()}_significant_day', None)()

    def significant_shabbos(self) -> Optional[str]:
        if self.day_of_week != 7:
            return None
        if self.jewish_month == 1:
            if self.jewish_day == 1:
                return self.SIGNIFICANT_SHABBOS.parshas_hachodesh.name
            elif self.jewish_day in range(8, 15):
                return self.SIGNIFICANT_SHABBOS.shabbos_hagadol.name
        elif self.jewish_month == 7 and self.jewish_day in range(3, 10):
            return self.SIGNIFICANT_SHABBOS.shabbos_shuva.name
        elif self.jewish_month == (self.months_in_jewish_year() - 1) and self.jewish_day in range(25, 31):
            return self.SIGNIFICANT_SHABBOS.parshas_shekalim.name
        elif self.jewish_month == self.months_in_jewish_year():
            if self.jewish_day == 1:
                return self.SIGNIFICANT_SHABBOS.parshas_shekalim.name
            elif self.jewish_day in range(7, 14):
                return self.SIGNIFICANT_SHABBOS.parshas_zachor.name
            elif self.jewish_day in range(17, 24):
                return self.SIGNIFICANT_SHABBOS.parshas_parah.name
            elif self.jewish_day in range(24, 30):
                return self.SIGNIFICANT_SHABBOS.parshas_hachodesh.name

    def is_assur_bemelacha(self) -> bool:
        """
        This method will return `True` if this date has a melacha (work) prohibition.
        """
        return self.day_of_week == 7 or self.is_yom_tov_assur_bemelacha()

    def is_tomorrow_assur_bemelacha(self) -> bool:
        """
        This method will return `True` if tomorrow has a melacha (work) prohibition.
        """
        return self.day_of_week == 6 or self.is_erev_yom_tov() or self.is_erev_yom_tov_sheni()

    def has_candle_lighting(self) -> bool:
        """
        This method will return `True` if this date has candle lighting.
        """
        return self.is_tomorrow_assur_bemelacha()

    def has_delayed_candle_lighting(self) -> bool:
        """
        This method will return `True` if this date has delayed candle lighting.
        """
        return self.day_of_week != 6 and self.has_candle_lighting() and self.is_assur_bemelacha()

    def is_yom_tov(self) -> bool:
        """
        This method will return `True` if this date is a Yom Tov.
        """
        sd = self.significant_day()
        return sd is not None \
            and not sd.startswith('erev_') \
            and (not self.is_taanis() or sd == self.SIGNIFICANT_DAYS.yom_kippur.name)

    def is_yom_tov_assur_bemelacha(self) -> bool:
        """
        This method will return `True` if this date is a Yom Tov that has a melacha (work) prohibition.
        """
        return self.significant_day() in [self.SIGNIFICANT_DAYS.pesach.name, self.SIGNIFICANT_DAYS.shavuos.name, self.SIGNIFICANT_DAYS.rosh_hashana.name, self.SIGNIFICANT_DAYS.yom_kippur.name,
                                          self.SIGNIFICANT_DAYS.succos.name, self.SIGNIFICANT_DAYS.shemini_atzeres.name, self.SIGNIFICANT_DAYS.simchas_torah.name]

    def is_erev_yom_tov(self) -> bool:
        """
        This method will return `True` if this date is Erev Yom Tov.
        """
        sd = self.significant_day()
        return sd is not None and (sd.startswith('erev_')
                                   or sd == self.SIGNIFICANT_DAYS.hoshana_rabbah.name
                                   or (sd == self.SIGNIFICANT_DAYS.chol_hamoed_pesach.name and self.jewish_day == 20))

    def is_yom_tov_sheni(self) -> bool:
        """
        This method will return `True` if this date is Yom Tov Sheni.
        """
        return ((self.jewish_month == 7 and self.jewish_day == 2)
                or (not self.in_israel and (
                    (self.jewish_month == 7 and self.jewish_day in [16, 23]) or
                    (self.jewish_month == 1 and self.jewish_day in [16, 22]) or
                    (self.jewish_month == 3 and self.jewish_day == 7)
                )))

    def is_erev_yom_tov_sheni(self) -> bool:
        """
        This method will return `True` if this date is Erev Yom Tov Sheni.
        """
        return ((self.jewish_month == 7 and self.jewish_day == 1)
                or (not self.in_israel and (
                    (self.jewish_month == 7 and self.jewish_day in [15, 22]) or
                    (self.jewish_month == 1 and self.jewish_day in [15, 21]) or
                    (self.jewish_month == 3 and self.jewish_day == 6)
                )))

    def is_chol_hamoed(self) -> bool:
        """
        This method will return `True` if this date is Chol Hamoed.
        """
        sd = self.significant_day()
        return sd is not None and (sd.startswith('chol_hamoed_') or sd == self.SIGNIFICANT_DAYS.hoshana_rabbah.name)

    def is_taanis(self) -> bool:
        """
        This method will return `True` if this date is a Taanis.
        """
        return self.significant_day() in [self.SIGNIFICANT_DAYS.seventeen_of_tammuz.name , self.SIGNIFICANT_DAYS.tisha_beav.name, self.SIGNIFICANT_DAYS.tzom_gedalyah.name,
                                          self.SIGNIFICANT_DAYS.yom_kippur.name, self.SIGNIFICANT_DAYS.tenth_of_teves.name, self.SIGNIFICANT_DAYS.taanis_esther.name]

    def is_taanis_bechorim(self) -> bool:
        """
        This method will return `True` if this date is Taanis Bechorim.
        """
        return ((self.day_of_week != 7 and self.jewish_day == 14 and self.jewish_month == 1) or
                (self.day_of_week == 5 and self.jewish_day == 12 and self.jewish_month == 1))

    def is_shabbos_mevorchim(self) -> bool:
        """
        This method will return `True` if this date is a Shabbos Mevorchim.
        """
        return self.day_of_week == 7 and self.jewish_month != 6 and self.jewish_day in range(23, 30)

    def is_rosh_chodesh(self) -> bool:
        """
        This method will return `True` if this date is Rosh Chodesh.
        """
        return self.jewish_day == 30 or (self.jewish_day == 1 and self.jewish_month != 7)

    def is_erev_rosh_chodesh(self) -> bool:
        """
        This method will return `True` if this date is Erev Rosh Chodesh.
        """
        return self.jewish_day == 29 and self.jewish_month != 6

    def is_chanukah(self) -> bool:
        """
        This method will return `True` if this date is Chanukah.
        """
        return self.significant_day() == self.SIGNIFICANT_DAYS.chanukah.name

    def day_of_chanukah(self) -> Optional[int]:
        """
        This method will what day of Chanukah this date is, starting with `1`.
        If this date is not Chanukah, this method will return `None`.
        """
        if not self.is_chanukah():
            return None

        if self.jewish_month_name() == self.MONTHS.kislev.name:
            return self.jewish_day - 24
        else:
            return self.jewish_day + (5 if self.is_kislev_short() else 6)

    def day_of_omer(self) -> Optional[int]:
        """
        This method will return what day of the Omer this date is, starting with `1`.
        If this date is not during the Omer, this method will return `None`.
        """
        
        month_name = self.jewish_month_name()
        if month_name == self.MONTHS.nissan.name:
            return self.jewish_day - 15 if self.jewish_day > 15 else None
        elif month_name == self.MONTHS.iyar.name:
            return self.jewish_day + 15
        elif month_name == self.MONTHS.sivan.name:
            return self.jewish_day + 44 if self.jewish_day < 6 else None
        else:
            return None

    def molad_as_datetime(self) -> datetime:
        """
        This method will return the molad of this month as a `datetime` object.
        """
        m = self.molad()
        location_name = 'Jerusalem, Israel'
        latitude = 31.778  # Har Habayis latitude
        longitude = 35.2354  # Har Habayis longitude
        zone = tz.gettz('Asia/Jerusalem')

        geo = GeoLocation(location_name, latitude, longitude, zone)
        seconds = m.molad_chalakim * 10 / 3.0
        seconds, microseconds = divmod(seconds * 10**6, 10**6)
        # molad as local mean time
        time = datetime(m.gregorian_year, m.gregorian_month, m.gregorian_day,
                        m.molad_hours, m.molad_minutes, int(seconds), int(microseconds),
                        tzinfo=tz.gettz('Etc/GMT-2'))
        # molad as Jerusalem standard time
        micro_offset = geo.local_mean_time_offset() * 1000
        time -= timedelta(microseconds=micro_offset)
        # molad as UTC
        return time.astimezone(tz.UTC)

    def techilas_zman_kiddush_levana_3_days(self) -> datetime:
        """
        This method will return the earliest time for Kiddush Levana for this month as a `datetime` object based on the opinion that one may only say Kiddush Levana after 3 days.
        """
        return self.molad_as_datetime() + timedelta(3)

    def techilas_zman_kiddush_levana_7_days(self) -> datetime:
        """
        This method will return the earliest time for Kiddush Levana for this month as a `datetime` object based on the opinion that one may only say Kiddush Levana after 7 days.
        """
        return self.molad_as_datetime() + timedelta(7)

    def sof_zman_kiddush_levana_between_moldos(self) -> datetime:
        """
        This method will return the latest time for Kiddush Levana for this month as a `datetime` object based on the opinion that one may say Kiddush Levana between moldos.
        """
        half_molad_in_seconds = self.CHALAKIM_PER_MONTH * 10 / 6.0
        return self.molad_as_datetime() + timedelta(microseconds=half_molad_in_seconds * 10**6)

    def sof_zman_kiddush_levana_15_days(self) -> datetime:
        """
        This method will return the latest time for Kiddush Levana for this month as a `datetime` object based on the opinion that one may say Kiddush Levana for up to 15 days.
        """
        return self.molad_as_datetime() + timedelta(15)

    def _nissan_significant_day(self) -> Optional[str]:
        pesach = [15, 21]
        if not self.in_israel:
            pesach += [16, 22]

        if self.jewish_day == 14:
            return self.SIGNIFICANT_DAYS.erev_pesach.name
        elif self.jewish_day in pesach:
            return self.SIGNIFICANT_DAYS.pesach.name
        elif self.jewish_day in range(16,21):
            return self.SIGNIFICANT_DAYS.chol_hamoed_pesach.name
        elif self.use_modern_holidays:
            if (self.jewish_day == 26 and self.day_of_week == 5) \
                    or (self.jewish_day == 27 and self.day_of_week not in [1, 6]) \
                    or (self.jewish_day == 28 and self.day_of_week == 2):
                return self.SIGNIFICANT_DAYS.yom_hashoah.name

    def _iyar_significant_day(self) -> Optional[str]:
        if self.jewish_day == 14:
            return self.SIGNIFICANT_DAYS.pesach_sheni.name
        elif self.jewish_day == 18:
            return self.SIGNIFICANT_DAYS.lag_baomer.name
        elif self.use_modern_holidays:
            # Note that this logic follows the current rules, which were last revised in 5764.
            # The calculations for years prior may not reflect the actual dates observed at that time.
            if (self.jewish_day in [2, 3] and self.day_of_week == 4) \
                    or (self.jewish_day == 4 and self.day_of_week == 3) \
                    or (self.jewish_day == 5 and self.day_of_week == 2):
                return self.SIGNIFICANT_DAYS.yom_hazikaron.name
            elif (self.jewish_day in [3, 4] and self.day_of_week == 5) \
                    or (self.jewish_day == 5 and self.day_of_week == 4) \
                    or (self.jewish_day == 6 and self.day_of_week == 3):
                return self.SIGNIFICANT_DAYS.yom_haatzmaut.name
            elif self.jewish_day == 28:
                return self.SIGNIFICANT_DAYS.yom_yerushalayim.name

    def _sivan_significant_day(self) -> Optional[str]:
        shavuos = [6]
        if not self.in_israel:
            shavuos += [7]

        if self.jewish_day == 5:
            return self.SIGNIFICANT_DAYS.erev_shavuos.name
        elif self.jewish_day in shavuos:
            return self.SIGNIFICANT_DAYS.shavuos.name

    def _tammuz_significant_day(self) -> Optional[str]:
        if (self.jewish_day == 17 and self.day_of_week != 7) \
                or (self.jewish_day == 18 and self.day_of_week == 1):
            return self.SIGNIFICANT_DAYS.seventeen_of_tammuz.name

    def _av_significant_day(self) -> Optional[str]:
        if (self.jewish_day == 9 and self.day_of_week != 7) \
                or (self.jewish_day == 10 and self.day_of_week == 1):
            return self.SIGNIFICANT_DAYS.tisha_beav.name
        elif self.jewish_day == 15:
            return self.SIGNIFICANT_DAYS.tu_beav.name

    def _elul_significant_day(self) -> Optional[str]:
        if self.jewish_day == 29:
            return self.SIGNIFICANT_DAYS.erev_rosh_hashana.name

    def _tishrei_significant_day(self) -> Optional[str]:
        succos = [15]
        if not self.in_israel:
            succos += [16]

        if self.jewish_day in [1, 2]:
            return self.SIGNIFICANT_DAYS.rosh_hashana.name
        elif (self.jewish_day == 3 and self.day_of_week != 7) \
                or (self.jewish_day == 4 and self.day_of_week == 1):
            return self.SIGNIFICANT_DAYS.tzom_gedalyah.name
        elif self.jewish_day == 9:
            return self.SIGNIFICANT_DAYS.erev_yom_kippur.name
        elif self.jewish_day == 10:
            return self.SIGNIFICANT_DAYS.yom_kippur.name
        elif self.jewish_day == 14:
            return self.SIGNIFICANT_DAYS.erev_succos.name
        elif self.jewish_day in succos:
            return self.SIGNIFICANT_DAYS.succos.name
        elif self.jewish_day in range(16,21):
            return self.SIGNIFICANT_DAYS.chol_hamoed_succos.name
        elif self.jewish_day == 21:
            return self.SIGNIFICANT_DAYS.hoshana_rabbah.name
        elif self.jewish_day == 22:
            return self.SIGNIFICANT_DAYS.shemini_atzeres.name
        elif self.jewish_day == 23 and not self.in_israel:
            return self.SIGNIFICANT_DAYS.simchas_torah.name

    def _cheshvan_significant_day(self) -> None:
        return None

    def _kislev_significant_day(self) -> Optional[str]:
        if self.jewish_day >= 25:
            return self.SIGNIFICANT_DAYS.chanukah.name

    def _teves_significant_day(self) -> Optional[str]:
        chanukah = [1,2]
        if self.is_kislev_short():
            chanukah += [3]

        if self.jewish_day in chanukah:
            return self.SIGNIFICANT_DAYS.chanukah.name
        elif self.jewish_day == 10:
            return self.SIGNIFICANT_DAYS.tenth_of_teves.name

    def _shevat_significant_day(self) -> Optional[str]:
        if self.jewish_day == 15:
            return self.SIGNIFICANT_DAYS.tu_beshvat.name

    def _adar_significant_day(self) -> Optional[str]:
        if self.is_jewish_leap_year():
            if self.jewish_day == 14:
                return self.SIGNIFICANT_DAYS.purim_katan.name
            elif self.jewish_day == 15:
                return self.SIGNIFICANT_DAYS.shushan_purim_katan.name
        else:
            return self._purim_significant_day()

    def _adar_ii_significant_day(self) -> Optional[str]:
        return self._purim_significant_day()

    def _purim_significant_day(self) -> Optional[str]:
        if (self.jewish_day == 13 and self.day_of_week != 7) \
                or (self.jewish_day == 11 and self.day_of_week == 5):
            return self.SIGNIFICANT_DAYS.taanis_esther.name
        elif self.jewish_day == 14:
            return self.SIGNIFICANT_DAYS.purim.name
        elif self.jewish_day == 15:
            return self.SIGNIFICANT_DAYS.shushan_purim.name