from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QLabel, QMessageBox, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt

# ISO 3166-1 country names, sorted alphabetically
COUNTRY_LIST = [
    "",
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda",
    "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain",
    "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria",
    "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada",
    "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros",
    "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic",
    "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica",
    "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea",
    "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France",
    "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada",
    "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras",
    "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland",
    "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya",
    "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho",
    "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar",
    "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands",
    "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco",
    "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia",
    "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger",
    "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan",
    "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru",
    "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda",
    "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines",
    "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal",
    "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia",
    "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan",
    "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria",
    "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo",
    "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu",
    "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States",
    "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam",
    "Yemen", "Zambia", "Zimbabwe",
]

# ISO 3166-1 alpha-2 codes matching COUNTRY_LIST entries
COUNTRY_CODE_MAP: dict[str, str] = {
    "Afghanistan": "AF", "Albania": "AL", "Algeria": "DZ", "Andorra": "AD",
    "Angola": "AO", "Antigua and Barbuda": "AG", "Argentina": "AR", "Armenia": "AM",
    "Australia": "AU", "Austria": "AT", "Azerbaijan": "AZ", "Bahamas": "BS",
    "Bahrain": "BH", "Bangladesh": "BD", "Barbados": "BB", "Belarus": "BY",
    "Belgium": "BE", "Belize": "BZ", "Benin": "BJ", "Bhutan": "BT",
    "Bolivia": "BO", "Bosnia and Herzegovina": "BA", "Botswana": "BW", "Brazil": "BR",
    "Brunei": "BN", "Bulgaria": "BG", "Burkina Faso": "BF", "Burundi": "BI",
    "Cabo Verde": "CV", "Cambodia": "KH", "Cameroon": "CM", "Canada": "CA",
    "Central African Republic": "CF", "Chad": "TD", "Chile": "CL", "China": "CN",
    "Colombia": "CO", "Comoros": "KM", "Congo": "CG", "Costa Rica": "CR",
    "Croatia": "HR", "Cuba": "CU", "Cyprus": "CY", "Czech Republic": "CZ",
    "Democratic Republic of the Congo": "CD", "Denmark": "DK", "Djibouti": "DJ",
    "Dominica": "DM", "Dominican Republic": "DO", "Ecuador": "EC", "Egypt": "EG",
    "El Salvador": "SV", "Equatorial Guinea": "GQ", "Eritrea": "ER", "Estonia": "EE",
    "Eswatini": "SZ", "Ethiopia": "ET", "Fiji": "FJ", "Finland": "FI", "France": "FR",
    "Gabon": "GA", "Gambia": "GM", "Georgia": "GE", "Germany": "DE", "Ghana": "GH",
    "Greece": "GR", "Grenada": "GD", "Guatemala": "GT", "Guinea": "GN",
    "Guinea-Bissau": "GW", "Guyana": "GY", "Haiti": "HT", "Honduras": "HN",
    "Hungary": "HU", "Iceland": "IS", "India": "IN", "Indonesia": "ID", "Iran": "IR",
    "Iraq": "IQ", "Ireland": "IE", "Israel": "IL", "Italy": "IT", "Jamaica": "JM",
    "Japan": "JP", "Jordan": "JO", "Kazakhstan": "KZ", "Kenya": "KE",
    "Kiribati": "KI", "Kuwait": "KW", "Kyrgyzstan": "KG", "Laos": "LA",
    "Latvia": "LV", "Lebanon": "LB", "Lesotho": "LS", "Liberia": "LR",
    "Libya": "LY", "Liechtenstein": "LI", "Lithuania": "LT", "Luxembourg": "LU",
    "Madagascar": "MG", "Malawi": "MW", "Malaysia": "MY", "Maldives": "MV",
    "Mali": "ML", "Malta": "MT", "Marshall Islands": "MH", "Mauritania": "MR",
    "Mauritius": "MU", "Mexico": "MX", "Micronesia": "FM", "Moldova": "MD",
    "Monaco": "MC", "Mongolia": "MN", "Montenegro": "ME", "Morocco": "MA",
    "Mozambique": "MZ", "Myanmar": "MM", "Namibia": "NA", "Nauru": "NR",
    "Nepal": "NP", "Netherlands": "NL", "New Zealand": "NZ", "Nicaragua": "NI",
    "Niger": "NE", "Nigeria": "NG", "North Korea": "KP", "North Macedonia": "MK",
    "Norway": "NO", "Oman": "OM", "Pakistan": "PK", "Palau": "PW",
    "Palestine": "PS", "Panama": "PA", "Papua New Guinea": "PG", "Paraguay": "PY",
    "Peru": "PE", "Philippines": "PH", "Poland": "PL", "Portugal": "PT",
    "Qatar": "QA", "Romania": "RO", "Russia": "RU", "Rwanda": "RW",
    "Saint Kitts and Nevis": "KN", "Saint Lucia": "LC",
    "Saint Vincent and the Grenadines": "VC", "Samoa": "WS", "San Marino": "SM",
    "Sao Tome and Principe": "ST", "Saudi Arabia": "SA", "Senegal": "SN",
    "Serbia": "RS", "Seychelles": "SC", "Sierra Leone": "SL", "Singapore": "SG",
    "Slovakia": "SK", "Slovenia": "SI", "Solomon Islands": "SB", "Somalia": "SO",
    "South Africa": "ZA", "South Korea": "KR", "South Sudan": "SS", "Spain": "ES",
    "Sri Lanka": "LK", "Sudan": "SD", "Suriname": "SR", "Sweden": "SE",
    "Switzerland": "CH", "Syria": "SY", "Taiwan": "TW", "Tajikistan": "TJ",
    "Tanzania": "TZ", "Thailand": "TH", "Timor-Leste": "TL", "Togo": "TG",
    "Tonga": "TO", "Trinidad and Tobago": "TT", "Tunisia": "TN", "Turkey": "TR",
    "Turkmenistan": "TM", "Tuvalu": "TV", "Uganda": "UG", "Ukraine": "UA",
    "United Arab Emirates": "AE", "United Kingdom": "GB", "United States": "US",
    "Uruguay": "UY", "Uzbekistan": "UZ", "Vanuatu": "VU", "Vatican City": "VA",
    "Venezuela": "VE", "Vietnam": "VN", "Yemen": "YE", "Zambia": "ZM",
    "Zimbabwe": "ZW",
}

COL_IMAGE = 0
COL_LAT = 1
COL_LNG = 2
COL_COUNTRY = 3
COL_CITY = 4


class GeoReviewDialog(QDialog):
    """
    Review and edit reverse geocode results before writing to image EXIF.

    Args:
        results: list of dicts with keys:
            image_path (str), filename (str), lat (float), lng (float),
            city (str), country (str)
        parent: parent QWidget
    """

    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Review Geocode Results")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumWidth(850)

        self._results = results
        self._setup_ui()
        self._populate_table()

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.adjustSize()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "Review geocode results. Edit Latitude, Longitude, Country, and City before saving."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Image", "Latitude", "Longitude", "Country", "City"]
        )
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked |
            QTableWidget.EditTrigger.SelectedClicked |
            QTableWidget.EditTrigger.EditKeyPressed
        )
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Populate
    # ------------------------------------------------------------------

    def _populate_table(self):
        self.table.setRowCount(len(self._results))

        for row, entry in enumerate(self._results):
            # Image name — read only
            name_item = QTableWidgetItem(entry.get("filename", ""))
            name_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            )
            self.table.setItem(row, COL_IMAGE, name_item)

            # Latitude
            lat_val = entry.get("lat", "")
            lat_text = f"{lat_val:.6f}" if isinstance(lat_val, float) else str(lat_val)
            self.table.setItem(row, COL_LAT, QTableWidgetItem(lat_text))

            # Longitude
            lng_val = entry.get("lng", "")
            lng_text = f"{lng_val:.6f}" if isinstance(lng_val, float) else str(lng_val)
            self.table.setItem(row, COL_LNG, QTableWidgetItem(lng_text))

            # Country — QComboBox
            combo = QComboBox()
            combo.addItems(COUNTRY_LIST)
            country = entry.get("country", "")
            idx = combo.findText(country, Qt.MatchFlag.MatchFixedString)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            else:
                # Geocoded country not in list — add it temporarily
                if country:
                    combo.insertItem(1, country)
                    combo.setCurrentIndex(1)
            self.table.setCellWidget(row, COL_COUNTRY, combo)

            # City
            city = entry.get("city", "")
            self.table.setItem(row, COL_CITY, QTableWidgetItem(city))

    # ------------------------------------------------------------------
    # Validation & save
    # ------------------------------------------------------------------

    def _on_save(self):
        for row in range(self.table.rowCount()):
            filename = self.table.item(row, COL_IMAGE).text()

            lat_text = (self.table.item(row, COL_LAT) or QTableWidgetItem("")).text().strip()
            lng_text = (self.table.item(row, COL_LNG) or QTableWidgetItem("")).text().strip()

            try:
                lat = float(lat_text)
            except ValueError:
                self._show_validation_error(row, filename, f"Invalid latitude: '{lat_text}'")
                return

            if not (-90.0 <= lat <= 90.0):
                self._show_validation_error(row, filename, f"Latitude {lat} out of range [-90, 90]")
                return

            try:
                lng = float(lng_text)
            except ValueError:
                self._show_validation_error(row, filename, f"Invalid longitude: '{lng_text}'")
                return

            if not (-180.0 <= lng <= 180.0):
                self._show_validation_error(row, filename, f"Longitude {lng} out of range [-180, 180]")
                return

        self.accept()

    def _show_validation_error(self, row, filename, message):
        self.table.selectRow(row)
        QMessageBox.warning(self, "Validation Error", f"Row {row + 1} ({filename}): {message}")

    # ------------------------------------------------------------------
    # Result extraction
    # ------------------------------------------------------------------

    def get_results(self):
        """
        Return list of dicts with edited values. Call after dialog accepted.

        Each dict: image_path (str), lat (float), lng (float),
                   country (str), country_code (str), city (str)
        """
        out = []
        for row in range(self.table.rowCount()):
            image_path = self._results[row]["image_path"]

            lat = float(self.table.item(row, COL_LAT).text().strip())
            lng = float(self.table.item(row, COL_LNG).text().strip())

            combo = self.table.cellWidget(row, COL_COUNTRY)
            country = combo.currentText() if combo else ""
            country_code = COUNTRY_CODE_MAP.get(country, "")

            city_item = self.table.item(row, COL_CITY)
            city = city_item.text().strip() if city_item else ""

            out.append({
                "image_path": image_path,
                "lat": lat,
                "lng": lng,
                "country": country,
                "country_code": country_code,
                "city": city,
            })
        return out
