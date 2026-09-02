import React, { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Routes, Route, Navigate, NavLink, useLocation } from "react-router-dom";
import axios from "axios";
import Member from "./pages/member.jsx";
import MembershipRequests from "./pages/membershipRequests.jsx";
import { API_BASE_URL } from "./api.js";
import {
  Building2,
  ChevronRight,
  CreditCard,
  HardHat,
  LayoutDashboard,
  PanelLeftClose,
  PanelLeftOpen,
  Sparkles,
  Trash2,
  UsersRound,
} from "lucide-react";


const CITY_OPTIONS = [
  { value: "Tehran", label: "Tehran" },
];

const TEHRAN_NEIGHBORHOOD_OPTIONS = [
  {
    "value": "13 Aban",
    "label": "13 Aban — سیزده آبان",
    "fa": "سیزده آبان",
    "avgPricePerSqm": 2110520
  },
  {
    "value": "15 Khordad",
    "label": "15 Khordad — پانزده خرداد",
    "fa": "پانزده خرداد",
    "avgPricePerSqm": 2463818
  },
  {
    "value": "30 Metri Ji",
    "label": "30 Metri Ji — سی متری جی",
    "fa": "سی متری جی",
    "avgPricePerSqm": 2554142
  },
  {
    "value": "Abbas Abad",
    "label": "Abbas Abad — عباس آباد",
    "fa": "عباس آباد",
    "avgPricePerSqm": 5777644
  },
  {
    "value": "Abdol Abad",
    "label": "Abdol Abad — عبدل آباد",
    "fa": "عبدل آباد",
    "avgPricePerSqm": 2348500
  },
  {
    "value": "Abousaeid",
    "label": "Abousaeid — ابوسعید",
    "fa": "ابوسعید",
    "avgPricePerSqm": 3343711
  },
  {
    "value": "Afsariyeh",
    "label": "Afsariyeh — افسریه",
    "fa": "افسریه",
    "avgPricePerSqm": 2791286
  },
  {
    "value": "Afsariyeh Junction",
    "label": "Afsariyeh Junction — سه راه افسریه",
    "fa": "سه راه افسریه",
    "avgPricePerSqm": 2043429
  },
  {
    "value": "Aghdasieh",
    "label": "Aghdasieh — اقدسیه",
    "fa": "اقدسیه",
    "avgPricePerSqm": 12447558
  },
  {
    "value": "Ahmadabad Mostofi Road",
    "label": "Ahmadabad Mostofi Road — جاده احمدآباد مستوفی",
    "fa": "جاده احمدآباد مستوفی",
    "avgPricePerSqm": 2066875
  },
  {
    "value": "Ajodanie",
    "label": "Ajodanie — آجودانیه",
    "fa": "آجودانیه",
    "avgPricePerSqm": 10945916
  },
  {
    "value": "Ali Abad",
    "label": "Ali Abad — علی آباد",
    "fa": "علی آباد",
    "avgPricePerSqm": 2216929
  },
  {
    "value": "Amin Abad",
    "label": "Amin Abad — امین آباد",
    "fa": "امین آباد",
    "avgPricePerSqm": 3250000
  },
  {
    "value": "Amin Hozour Junction",
    "label": "Amin Hozour Junction — سه راه امین حضور",
    "fa": "سه راه امین حضور",
    "avgPricePerSqm": 2552800
  },
  {
    "value": "Amin ol Molk",
    "label": "Amin ol Molk — امین الملک",
    "fa": "امین الملک",
    "avgPricePerSqm": 2233333
  },
  {
    "value": "Amir Abad",
    "label": "Amir Abad — امیرآباد",
    "fa": "امیرآباد",
    "avgPricePerSqm": 6215722
  },
  {
    "value": "Amir Kabir",
    "label": "Amir Kabir — امیرکبیر",
    "fa": "امیرکبیر",
    "avgPricePerSqm": 5200000
  },
  {
    "value": "Amiriyeh",
    "label": "Amiriyeh — امیریه",
    "fa": "امیریه",
    "avgPricePerSqm": 2913992
  },
  {
    "value": "Apadana",
    "label": "Apadana — آپادانا",
    "fa": "آپادانا",
    "avgPricePerSqm": 7828658
  },
  {
    "value": "Apadana Town",
    "label": "Apadana Town — شهرک آپادانا",
    "fa": "شهرک آپادانا",
    "avgPricePerSqm": 4396286
  },
  {
    "value": "Araghi",
    "label": "Araghi — شهیدعراقی",
    "fa": "شهیدعراقی",
    "avgPricePerSqm": 7294611
  },
  {
    "value": "Aref",
    "label": "Aref — عارف",
    "fa": "عارف",
    "avgPricePerSqm": 2887075
  },
  {
    "value": "Argentina Square",
    "label": "Argentina Square — میدان آرژانتین",
    "fa": "میدان آرژانتین",
    "avgPricePerSqm": 6637543
  },
  {
    "value": "Artesh",
    "label": "Artesh — بزرگراه ارتش",
    "fa": "بزرگراه ارتش",
    "avgPricePerSqm": 6368750,
    "aliases": [
      "Artesh (Lashkarak)",
      "بزرگراه ارتش (لشکرک)"
    ]
  },
  {
    "value": "Ashrafi Esfahani",
    "label": "Ashrafi Esfahani — اشرفی اصفهانی",
    "fa": "اشرفی اصفهانی",
    "avgPricePerSqm": 4891238,
    "aliases": [
      "Ashrafi Esfahan (Sadeghieh ta Hakim)",
      "Ashrafi Esfahani (Bolvar ta Hakim)",
      "اشرفی اصفهانی( از میدان صادقیه تا حکیم)",
      "اشرفی اصفهانی(از بلوار سیمون بولیوار تا حکیم)"
    ]
  },
  {
    "value": "Asia Boulevard",
    "label": "Asia Boulevard — بلوار آسیا",
    "fa": "بلوار آسیا",
    "avgPricePerSqm": 4907692
  },
  {
    "value": "Atabak",
    "label": "Atabak — اتابک",
    "fa": "اتابک",
    "avgPricePerSqm": 2626425
  },
  {
    "value": "Ayatollah",
    "label": "Ayatollah — امام خمینی",
    "fa": "امام خمینی",
    "avgPricePerSqm": 2863958,
    "aliases": [
      "Ayatollah (Navab-Yadegar)",
      "امام خمینی(از نواب تا یادگار)"
    ]
  },
  {
    "value": "Ayatollah Kashani",
    "label": "Ayatollah Kashani — آیت اله کاشانی",
    "fa": "آیت اله کاشانی",
    "avgPricePerSqm": 5027664
  },
  {
    "value": "Ayatollah Saeedi",
    "label": "Ayatollah Saeedi — آیت الله سعیدی",
    "fa": "آیت الله سعیدی",
    "avgPricePerSqm": 2304000
  },
  {
    "value": "Azadegan",
    "label": "Azadegan — آزادگان",
    "fa": "آزادگان",
    "avgPricePerSqm": 2179464,
    "aliases": [
      "آزادگان(از آیت الله سعیدی تا جاده قدیم کرج)"
    ]
  },
  {
    "value": "Azadi",
    "label": "Azadi — آزادی",
    "fa": "آزادی",
    "avgPricePerSqm": 3812761,
    "aliases": [
      "Azadi (Ta navab)",
      "آزادی(از میدان انقلاب تا نواب)",
      "آزادی(از نواب تا میدان آزادی)"
    ]
  },
  {
    "value": "Azari",
    "label": "Azari — آذری",
    "fa": "آذری",
    "avgPricePerSqm": 2234342
  },
  {
    "value": "Azerbaijan",
    "label": "Azerbaijan — آذربایجان",
    "fa": "آذربایجان",
    "avgPricePerSqm": 3330337
  },
  {
    "value": "Bab Homayoun",
    "label": "Bab Homayoun — باب همایون",
    "fa": "باب همایون",
    "avgPricePerSqm": 4000000
  },
  {
    "value": "Bagh Ferdows",
    "label": "Bagh Ferdows — باغ فردوس",
    "fa": "باغ فردوس",
    "avgPricePerSqm": 15184615
  },
  {
    "value": "Bagh Khazaneh",
    "label": "Bagh Khazaneh — باغ خزانه",
    "fa": "باغ خزانه",
    "avgPricePerSqm": 2600000
  },
  {
    "value": "Baharestan",
    "label": "Baharestan — بهارستان",
    "fa": "بهارستان",
    "avgPricePerSqm": 3337646
  },
  {
    "value": "Bahman Square",
    "label": "Bahman Square — میدان بهمن",
    "fa": "میدان بهمن",
    "avgPricePerSqm": 2350000
  },
  {
    "value": "Bani Hashem",
    "label": "Bani Hashem — بنی هاشم",
    "fa": "بنی هاشم",
    "avgPricePerSqm": 5004609
  },
  {
    "value": "Baradaran Hasani",
    "label": "Baradaran Hasani — برادران حسنی",
    "fa": "برادران حسنی",
    "avgPricePerSqm": 2371389,
    "aliases": [
      "برادران حسنی(قلعه مرغی)"
    ]
  },
  {
    "value": "Bazaar",
    "label": "Bazaar — بازار",
    "fa": "بازار",
    "avgPricePerSqm": 2500000
  },
  {
    "value": "Beryanak",
    "label": "Beryanak — بریانک",
    "fa": "بریانک",
    "avgPricePerSqm": 2494054
  },
  {
    "value": "Besat Highway",
    "label": "Besat Highway — بزرگراه بعثت",
    "fa": "بزرگراه بعثت",
    "avgPricePerSqm": 2291467,
    "aliases": [
      "بزرگراه بعثت(از فداییان تا سه راه افسریه)",
      "بزرگراه بعثت(از میدان بهمن تا فداییان اسلام)"
    ]
  },
  {
    "value": "Bisim",
    "label": "Bisim — بی سیم",
    "fa": "بی سیم",
    "avgPricePerSqm": 2434350
  },
  {
    "value": "Bokharest",
    "label": "Bokharest — بخارست",
    "fa": "بخارست",
    "avgPricePerSqm": 6842857
  },
  {
    "value": "Boloursazi",
    "label": "Boloursazi — بلورسازی",
    "fa": "بلورسازی",
    "avgPricePerSqm": 2117200
  },
  {
    "value": "Bolvar Ferdows",
    "label": "Bolvar Ferdows — بلوار فردوس",
    "fa": "بلوار فردوس",
    "avgPricePerSqm": 4882526,
    "aliases": [
      "Bolvar Ferdos"
    ]
  },
  {
    "value": "Cheshmeh Ali",
    "label": "Cheshmeh Ali — چشمه علی",
    "fa": "چشمه علی",
    "avgPricePerSqm": 3000000
  },
  {
    "value": "Chitgar",
    "label": "Chitgar — چیتگر",
    "fa": "چیتگر",
    "avgPricePerSqm": 3707974
  },
  {
    "value": "Chitsazi",
    "label": "Chitsazi — چیت سازی",
    "fa": "چیت سازی",
    "avgPricePerSqm": 1538000
  },
  {
    "value": "College Crossroad",
    "label": "College Crossroad — چهارراه کالج",
    "fa": "چهارراه کالج",
    "avgPricePerSqm": 4537250
  },
  {
    "value": "Dabestan",
    "label": "Dabestan — دبستان",
    "fa": "دبستان",
    "avgPricePerSqm": 4608839
  },
  {
    "value": "Damavand",
    "label": "Damavand — دماوند",
    "fa": "دماوند",
    "avgPricePerSqm": 3082118,
    "aliases": [
      "دماوند(از Imam Hossein تا Vahidieh)",
      "دماوند(از میدان امام حسین تا وحیدیه)"
    ]
  },
  {
    "value": "Dampezeshki",
    "label": "Dampezeshki — دامپزشکی",
    "fa": "دامپزشکی",
    "avgPricePerSqm": 3091669,
    "aliases": [
      "دامپزشکی(از نواب تا یادگار)",
      "دامپزشکی(از یادگار تا آیت الله سعیدی)"
    ]
  },
  {
    "value": "Darabad",
    "label": "Darabad — دارآباد",
    "fa": "دارآباد",
    "avgPricePerSqm": 6720374
  },
  {
    "value": "Darband",
    "label": "Darband — دربند",
    "fa": "دربند",
    "avgPricePerSqm": 7665612
  },
  {
    "value": "Daroos",
    "label": "Daroos — دروس",
    "fa": "دروس",
    "avgPricePerSqm": 9809326
  },
  {
    "value": "Darou",
    "label": "Darou — تولید دارو",
    "fa": "تولید دارو",
    "avgPricePerSqm": 2474460
  },
  {
    "value": "Daryan No",
    "label": "Daryan No — دریان نو",
    "fa": "دریان نو",
    "avgPricePerSqm": 5025325
  },
  {
    "value": "Dastgheib",
    "label": "Dastgheib — دستغیب",
    "fa": "دستغیب",
    "avgPricePerSqm": 2777754
  },
  {
    "value": "Delavaran",
    "label": "Delavaran — دلاوران",
    "fa": "دلاوران",
    "avgPricePerSqm": 3497247
  },
  {
    "value": "Deylaman",
    "label": "Deylaman — دیلمان",
    "fa": "دیلمان",
    "avgPricePerSqm": 2544100
  },
  {
    "value": "Dezashib",
    "label": "Dezashib — دزاشیب",
    "fa": "دزاشیب",
    "avgPricePerSqm": 8423981
  },
  {
    "value": "Dibaji Jonoobi",
    "label": "Dibaji Jonoobi — دیباجی جنوبی",
    "fa": "دیباجی جنوبی",
    "avgPricePerSqm": 8069431
  },
  {
    "value": "Dibaji Shomali",
    "label": "Dibaji Shomali — دیباجی شمالی",
    "fa": "دیباجی شمالی",
    "avgPricePerSqm": 12704588
  },
  {
    "value": "Dolab",
    "label": "Dolab — دولاب",
    "fa": "دولاب",
    "avgPricePerSqm": 2612250
  },
  {
    "value": "Dolat",
    "label": "Dolat — دولت",
    "fa": "دولت",
    "avgPricePerSqm": 7834652
  },
  {
    "value": "Dolat Abad",
    "label": "Dolat Abad — دولت آباد",
    "fa": "دولت آباد",
    "avgPricePerSqm": 2495462,
    "aliases": [
      "Dolat آباد"
    ]
  },
  {
    "value": "Ebn Babouyeh",
    "label": "Ebn Babouyeh — ابن بابویه",
    "fa": "ابن بابویه",
    "avgPricePerSqm": 2483000
  },
  {
    "value": "Ekbatan",
    "label": "Ekbatan — شهرک اکباتان",
    "fa": "شهرک اکباتان",
    "avgPricePerSqm": 4662507
  },
  {
    "value": "Ekhtiarieh",
    "label": "Ekhtiarieh — اختیاریه",
    "fa": "اختیاریه",
    "avgPricePerSqm": 7021052
  },
  {
    "value": "Elahieh",
    "label": "Elahieh — الهیه",
    "fa": "الهیه",
    "avgPricePerSqm": 14832319
  },
  {
    "value": "Enghelab",
    "label": "Enghelab — انقلاب",
    "fa": "انقلاب",
    "avgPricePerSqm": 4027259,
    "aliases": [
      "انقلاب(از Piche Shemran تا Imam Hossein)",
      "انقلاب(از Piche Shemran تا چهارراه ولیعصر)",
      "انقلاب(از پیچ شمیران تا میدان امام حسین)",
      "انقلاب(از پیچ شمیران تا چهارراه ولیعصر)",
      "انقلاب(از چهارراه ولیعصر تا میدان انقلاب)"
    ]
  },
  {
    "value": "Esfahanak",
    "label": "Esfahanak — اصفهانک",
    "fa": "اصفهانک",
    "avgPricePerSqm": 2348750
  },
  {
    "value": "Eskandari Jonubi",
    "label": "Eskandari Jonubi — اسکندری جنوبی",
    "fa": "اسکندری جنوبی",
    "avgPricePerSqm": 3097565
  },
  {
    "value": "Eskandari Shomali",
    "label": "Eskandari Shomali — اسکندری شمالی",
    "fa": "اسکندری شمالی",
    "avgPricePerSqm": 4180833
  },
  {
    "value": "Evin",
    "label": "Evin — اوین",
    "fa": "اوین",
    "avgPricePerSqm": 7924847
  },
  {
    "value": "Fadaeian-e Eslam",
    "label": "Fadaeian-e Eslam — فداییان اسلام",
    "fa": "فداییان اسلام",
    "avgPricePerSqm": 2729412,
    "aliases": [
      "فداییان اسلام(از آزادگان تا میدان شهر ری)"
    ]
  },
  {
    "value": "Fallah",
    "label": "Fallah — فلاح",
    "fa": "فلاح",
    "avgPricePerSqm": 2187277
  },
  {
    "value": "Farahzad",
    "label": "Farahzad — فرحزاد",
    "fa": "فرحزاد",
    "avgPricePerSqm": 6107299
  },
  {
    "value": "Farjam Gharbi",
    "label": "Farjam Gharbi — فرجام غربی",
    "fa": "فرجام غربی",
    "avgPricePerSqm": 4101737,
    "aliases": [
      "فرجام غربی( تا شهید باقری)"
    ]
  },
  {
    "value": "Farmanieh",
    "label": "Farmanieh — فرمانیه",
    "fa": "فرمانیه",
    "avgPricePerSqm": 11442237
  },
  {
    "value": "Fatemi",
    "label": "Fatemi — فاطمی",
    "fa": "فاطمی",
    "avgPricePerSqm": 5663442
  },
  {
    "value": "Fath Square",
    "label": "Fath Square — میدان فتح",
    "fa": "میدان فتح",
    "avgPricePerSqm": 2700000
  },
  {
    "value": "Ferdowsi",
    "label": "Ferdowsi — فردوسی",
    "fa": "فردوسی",
    "avgPricePerSqm": 4223778
  },
  {
    "value": "Ferdowsi Square",
    "label": "Ferdowsi Square — میدان فردوسی",
    "fa": "میدان فردوسی",
    "avgPricePerSqm": 3803056
  },
  {
    "value": "Fereshteh",
    "label": "Fereshteh — فرشته",
    "fa": "فرشته",
    "avgPricePerSqm": 15921716
  },
  {
    "value": "Gandhi",
    "label": "Gandhi — گاندی",
    "fa": "گاندی",
    "avgPricePerSqm": 8474224
  },
  {
    "value": "Ghaem Magham Farahani",
    "label": "Ghaem Magham Farahani — قائم مقام فراهانی",
    "fa": "قائم مقام فراهانی",
    "avgPricePerSqm": 5690686
  },
  {
    "value": "Ghaleh Morghi",
    "label": "Ghaleh Morghi — قلعه مرغی",
    "fa": "قلعه مرغی",
    "avgPricePerSqm": 2318500,
    "aliases": [
      "قلعه مرغی(بوستان ولایت)"
    ]
  },
  {
    "value": "Ghanat Kosar",
    "label": "Ghanat Kosar — قنات کوثر",
    "fa": "قنات کوثر",
    "avgPricePerSqm": 4590746
  },
  {
    "value": "Ghasr Dasht",
    "label": "Ghasr Dasht — قصرالدشت",
    "fa": "قصرالدشت",
    "avgPricePerSqm": 2931192
  },
  {
    "value": "Ghasr Firouzeh",
    "label": "Ghasr Firouzeh — قصر فیروزه",
    "fa": "قصر فیروزه",
    "avgPricePerSqm": 2600000
  },
  {
    "value": "Gheitarie",
    "label": "Gheitarie — قیطریه",
    "fa": "قیطریه",
    "avgPricePerSqm": 8919528
  },
  {
    "value": "Gholhak",
    "label": "Gholhak — قلهک",
    "fa": "قلهک",
    "avgPricePerSqm": 7868950
  },
  {
    "value": "Gisha",
    "label": "Gisha — گیشا",
    "fa": "گیشا",
    "avgPricePerSqm": 6751542
  },
  {
    "value": "Golbarg",
    "label": "Golbarg — گلبرگ",
    "fa": "گلبرگ",
    "avgPricePerSqm": 3826488
  },
  {
    "value": "Gomrok",
    "label": "Gomrok — گمرک",
    "fa": "گمرک",
    "avgPricePerSqm": 2174765
  },
  {
    "value": "Hafez",
    "label": "Hafez — حافظ",
    "fa": "حافظ",
    "avgPricePerSqm": 3888061
  },
  {
    "value": "Haft-e Tir",
    "label": "Haft-e Tir — هفت تیر",
    "fa": "هفت تیر",
    "avgPricePerSqm": 4639617
  },
  {
    "value": "Hakimieh",
    "label": "Hakimieh — حکیمیه",
    "fa": "حکیمیه",
    "avgPricePerSqm": 3969123
  },
  {
    "value": "Hashemi",
    "label": "Hashemi — هاشمی",
    "fa": "هاشمی",
    "avgPricePerSqm": 2850449,
    "aliases": [
      "هاشمی(از نواب تا یادگار)",
      "هاشمی(از یادگار تا آیت الله سعیدی)"
    ]
  },
  {
    "value": "Hassan Abad",
    "label": "Hassan Abad — حسن آباد",
    "fa": "حسن آباد",
    "avgPricePerSqm": 2780000
  },
  {
    "value": "Hefdah Shahrivar",
    "label": "Hefdah Shahrivar — هفده شهریور",
    "fa": "هفده شهریور",
    "avgPricePerSqm": 2904355,
    "aliases": [
      "Hefdah Shahrivar (Shohada)",
      "هفده شهریور(از شهدا تا شوش)"
    ]
  },
  {
    "value": "Helal Ahmar",
    "label": "Helal Ahmar — هلال احمر",
    "fa": "هلال احمر",
    "avgPricePerSqm": 2379136
  },
  {
    "value": "Hengam",
    "label": "Hengam — هنگام",
    "fa": "هنگام",
    "avgPricePerSqm": 3319020
  },
  {
    "value": "Heravi",
    "label": "Heravi — هروی",
    "fa": "هروی",
    "avgPricePerSqm": 6883892
  },
  {
    "value": "Horr Square",
    "label": "Horr Square — میدان حر",
    "fa": "میدان حر",
    "avgPricePerSqm": 3376174
  },
  {
    "value": "Imam Hossein",
    "label": "Imam Hossein — میدان امام حسین",
    "fa": "میدان امام حسین",
    "avgPricePerSqm": 2896136
  },
  {
    "value": "Imam Khomeini",
    "label": "Imam Khomeini — امام خمینی",
    "fa": "امام خمینی",
    "avgPricePerSqm": 3470062,
    "aliases": [
      "امام خمینی(از حسن آباد تا نواب)"
    ]
  },
  {
    "value": "Imamzadeh Hassan",
    "label": "Imamzadeh Hassan — امام زاده حسن",
    "fa": "امام زاده حسن",
    "avgPricePerSqm": 2425304
  },
  {
    "value": "Iran",
    "label": "Iran — ایران",
    "fa": "ایران",
    "avgPricePerSqm": 3749054
  },
  {
    "value": "Jamalzadeh",
    "label": "Jamalzadeh — جمالزاده",
    "fa": "جمالزاده",
    "avgPricePerSqm": 4436463
  },
  {
    "value": "Jannat Abad",
    "label": "Jannat Abad — جنت آباد",
    "fa": "جنت آباد",
    "avgPricePerSqm": 4833731
  },
  {
    "value": "Jashnvareh",
    "label": "Jashnvareh — جشنواره",
    "fa": "جشنواره",
    "avgPricePerSqm": 3279965
  },
  {
    "value": "Javadieh",
    "label": "Javadieh — جوادیه",
    "fa": "جوادیه",
    "avgPricePerSqm": 2190354
  },
  {
    "value": "Javanmard Ghassab",
    "label": "Javanmard Ghassab — جوانمرد قصاب",
    "fa": "جوانمرد قصاب",
    "avgPricePerSqm": 1954091
  },
  {
    "value": "Jeihoon",
    "label": "Jeihoon — جیحون",
    "fa": "جیحون",
    "avgPricePerSqm": 2792169
  },
  {
    "value": "Jolfa",
    "label": "Jolfa — جلفا",
    "fa": "جلفا",
    "avgPricePerSqm": 5987886
  },
  {
    "value": "Jomhouri",
    "label": "Jomhouri — جمهوری",
    "fa": "جمهوری",
    "avgPricePerSqm": 3671066,
    "aliases": [
      "جمهوری(از بهارستان تا حافظ)",
      "جمهوری(از حافظ تا میدان جمهوری)"
    ]
  },
  {
    "value": "Jordan",
    "label": "Jordan — جردن",
    "fa": "جردن",
    "avgPricePerSqm": 9355679
  },
  {
    "value": "Kamranieh",
    "label": "Kamranieh — کامرانیه",
    "fa": "کامرانیه",
    "avgPricePerSqm": 12242966
  },
  {
    "value": "Kan",
    "label": "Kan — کن",
    "fa": "کن",
    "avgPricePerSqm": 2585013
  },
  {
    "value": "Karim Khan",
    "label": "Karim Khan — کریم خان",
    "fa": "کریم خان",
    "avgPricePerSqm": 4916541
  },
  {
    "value": "Karoon",
    "label": "Karoon — کارون",
    "fa": "کارون",
    "avgPricePerSqm": 3078263
  },
  {
    "value": "Karvan Town",
    "label": "Karvan Town — شهرک کاروان",
    "fa": "شهرک کاروان",
    "avgPricePerSqm": 2130125
  },
  {
    "value": "Keshavarz",
    "label": "Keshavarz — بلوار کشاورز",
    "fa": "بلوار کشاورز",
    "avgPricePerSqm": 4819921
  },
  {
    "value": "Khaje Abdollah",
    "label": "Khaje Abdollah — خواجه عبداله",
    "fa": "خواجه عبداله",
    "avgPricePerSqm": 6274687
  },
  {
    "value": "Khaje Nasir",
    "label": "Khaje Nasir — خواجه نصیر",
    "fa": "خواجه نصیر",
    "avgPricePerSqm": 3400630
  },
  {
    "value": "Khaje Nezam",
    "label": "Khaje Nezam — خواجه نظام",
    "fa": "خواجه نظام",
    "avgPricePerSqm": 3177029
  },
  {
    "value": "Khani Abad No",
    "label": "Khani Abad No — خانی آباد نو",
    "fa": "خانی آباد نو",
    "avgPricePerSqm": 2553144
  },
  {
    "value": "Khavaran",
    "label": "Khavaran — خاوران",
    "fa": "خاوران",
    "avgPricePerSqm": 2338914
  },
  {
    "value": "Khayyam",
    "label": "Khayyam — خیام",
    "fa": "خیام",
    "avgPricePerSqm": 2216107
  },
  {
    "value": "Khazaneh",
    "label": "Khazaneh — خزانه",
    "fa": "خزانه",
    "avgPricePerSqm": 2425795
  },
  {
    "value": "Khorasan Square",
    "label": "Khorasan Square — میدان خراسان",
    "fa": "میدان خراسان",
    "avgPricePerSqm": 2453024
  },
  {
    "value": "Khosh",
    "label": "Khosh — خوش",
    "fa": "خوش",
    "avgPricePerSqm": 3133827
  },
  {
    "value": "Kian Shahr",
    "label": "Kian Shahr — کیانشهر",
    "fa": "کیانشهر",
    "avgPricePerSqm": 2150907
  },
  {
    "value": "Komeil",
    "label": "Komeil — کمیل",
    "fa": "کمیل",
    "avgPricePerSqm": 2556371
  },
  {
    "value": "Kooye Faraz",
    "label": "Kooye Faraz — کوی فراز",
    "fa": "کوی فراز",
    "avgPricePerSqm": 8693875
  },
  {
    "value": "Kordestan",
    "label": "Kordestan — کردستان",
    "fa": "کردستان",
    "avgPricePerSqm": 8545455
  },
  {
    "value": "Lalehzar",
    "label": "Lalehzar — لاله زار",
    "fa": "لاله زار",
    "avgPricePerSqm": 3500000
  },
  {
    "value": "Lashgar Crossroad",
    "label": "Lashgar Crossroad — چهارراه لشگر",
    "fa": "چهارراه لشگر",
    "avgPricePerSqm": 3043881
  },
  {
    "value": "Lavisan",
    "label": "Lavisan — لویزان",
    "fa": "لویزان",
    "avgPricePerSqm": 5509002
  },
  {
    "value": "Mahallati",
    "label": "Mahallati — بزرگراه محلاتی",
    "fa": "بزرگراه محلاتی",
    "avgPricePerSqm": 2829827,
    "aliases": [
      "Mahallati (Ahang)",
      "بزرگراه محلاتی ( آهنگ)"
    ]
  },
  {
    "value": "Mahmoodieh",
    "label": "Mahmoodieh — محمودیه",
    "fa": "محمودیه",
    "avgPricePerSqm": 14299776
  },
  {
    "value": "Majidieh Jonoobi",
    "label": "Majidieh Jonoobi — مجیدیه جنوبی",
    "fa": "مجیدیه جنوبی",
    "avgPricePerSqm": 3891295
  },
  {
    "value": "Majidieh Shomali",
    "label": "Majidieh Shomali — مجیدیه شمالی",
    "fa": "مجیدیه شمالی",
    "avgPricePerSqm": 4626423
  },
  {
    "value": "Malek Ashtar",
    "label": "Malek Ashtar — مالک اشتر",
    "fa": "مالک اشتر",
    "avgPricePerSqm": 2729466
  },
  {
    "value": "Manouchehri",
    "label": "Manouchehri — منوچهری",
    "fa": "منوچهری",
    "avgPricePerSqm": 3300000
  },
  {
    "value": "Marzdaran",
    "label": "Marzdaran — بلوارمرزداران",
    "fa": "بلوارمرزداران",
    "avgPricePerSqm": 6428680
  },
  {
    "value": "Masoudieh",
    "label": "Masoudieh — مسعودیه",
    "fa": "مسعودیه",
    "avgPricePerSqm": 2254388
  },
  {
    "value": "Mazandaran",
    "label": "Mazandaran — خیابان مازندران",
    "fa": "خیابان مازندران",
    "avgPricePerSqm": 3414813
  },
  {
    "value": "Mehrabad",
    "label": "Mehrabad — مهر آباد",
    "fa": "مهر آباد",
    "avgPricePerSqm": 2580364
  },
  {
    "value": "Mini City",
    "label": "Mini City — مینی سیتی",
    "fa": "مینی سیتی",
    "avgPricePerSqm": 6319471
  },
  {
    "value": "Mirdamad",
    "label": "Mirdamad — میرداماد",
    "fa": "میرداماد",
    "avgPricePerSqm": 8662864
  },
  {
    "value": "Mirzaye Shirazi",
    "label": "Mirzaye Shirazi — میرزای شیرازی",
    "fa": "میرزای شیرازی",
    "avgPricePerSqm": 5491711
  },
  {
    "value": "Moallem",
    "label": "Moallem — معلم",
    "fa": "معلم",
    "avgPricePerSqm": 3978392
  },
  {
    "value": "Mofatteh",
    "label": "Mofatteh — مفتح",
    "fa": "مفتح",
    "avgPricePerSqm": 4766615,
    "aliases": [
      "مفتح(از بهشتی تا هفت تیر)",
      "مفتح(از هفت تیر تا انقلاب)"
    ]
  },
  {
    "value": "Mojahedin-e Eslam",
    "label": "Mojahedin-e Eslam — مجاهدین اسلام",
    "fa": "مجاهدین اسلام",
    "avgPricePerSqm": 3985000
  },
  {
    "value": "Molavi",
    "label": "Molavi — مولوی",
    "fa": "مولوی",
    "avgPricePerSqm": 2219562,
    "aliases": [
      "Molavi (Ghiam)",
      "مولوی(از قیام تا وحدت اسلامی)",
      "مولوی(از وحدت اسلامی تا میدان رازی)"
    ]
  },
  {
    "value": "Molla Sadra",
    "label": "Molla Sadra — ملاصدرا",
    "fa": "ملاصدرا",
    "avgPricePerSqm": 8803735
  },
  {
    "value": "Moniriyeh",
    "label": "Moniriyeh — منیریه",
    "fa": "منیریه",
    "avgPricePerSqm": 3666643
  },
  {
    "value": "Moshiriyeh",
    "label": "Moshiriyeh — مشیریه",
    "fa": "مشیریه",
    "avgPricePerSqm": 2372370
  },
  {
    "value": "Mostafa Khomeini",
    "label": "Mostafa Khomeini — مصطفی خمینی",
    "fa": "مصطفی خمینی",
    "avgPricePerSqm": 2781778
  },
  {
    "value": "Motahari",
    "label": "Motahari — مطهری",
    "fa": "مطهری",
    "avgPricePerSqm": 5555985,
    "aliases": [
      "Motahari (Modarres-shariati)",
      "Motahari (Valiasr)",
      "مطهری (ازولیعصرتا مدرس)",
      "مطهری(از مدرس تا شریعتی)"
    ]
  },
  {
    "value": "Namjoo Gorgan",
    "label": "Namjoo Gorgan — نامجو",
    "fa": "نامجو",
    "avgPricePerSqm": 3183584,
    "aliases": [
      "نامجو(گرگان)"
    ]
  },
  {
    "value": "Narmak",
    "label": "Narmak — نارمک",
    "fa": "نارمک",
    "avgPricePerSqm": 4520692
  },
  {
    "value": "Naser Khosrow",
    "label": "Naser Khosrow — ناصرخسرو",
    "fa": "ناصرخسرو",
    "avgPricePerSqm": 2734000
  },
  {
    "value": "Navab",
    "label": "Navab — نواب",
    "fa": "نواب",
    "avgPricePerSqm": 2543321
  },
  {
    "value": "Nazi Abad",
    "label": "Nazi Abad — نازی آباد",
    "fa": "نازی آباد",
    "avgPricePerSqm": 3080446
  },
  {
    "value": "Nemat Abad",
    "label": "Nemat Abad — نعمت آباد",
    "fa": "نعمت آباد",
    "avgPricePerSqm": 2136250
  },
  {
    "value": "Nezam Abad",
    "label": "Nezam Abad — نظام آباد",
    "fa": "نظام آباد",
    "avgPricePerSqm": 3107998
  },
  {
    "value": "Niavaran",
    "label": "Niavaran — نیاوران",
    "fa": "نیاوران",
    "avgPricePerSqm": 11378085
  },
  {
    "value": "Niro Havaii",
    "label": "Niro Havaii — نیرو هوایی",
    "fa": "نیرو هوایی",
    "avgPricePerSqm": 4174936
  },
  {
    "value": "Niroo Daryaee",
    "label": "Niroo Daryaee — نیروی دریایی",
    "fa": "نیروی دریایی",
    "avgPricePerSqm": 4481288
  },
  {
    "value": "Nobonyad",
    "label": "Nobonyad — نوبنیاد",
    "fa": "نوبنیاد",
    "avgPricePerSqm": 9438889
  },
  {
    "value": "North Tajrish Square",
    "label": "North Tajrish Square — شمال میدان تجریش",
    "fa": "شمال میدان تجریش",
    "avgPricePerSqm": 10488065,
    "aliases": [
      "شمال میدان Tajrish"
    ]
  },
  {
    "value": "Omid Town",
    "label": "Omid Town — شهرک امید",
    "fa": "شهرک امید",
    "avgPricePerSqm": 7894967
  },
  {
    "value": "Ostad Moein",
    "label": "Ostad Moein — استاد معین",
    "fa": "استاد معین",
    "avgPricePerSqm": 3298310
  },
  {
    "value": "Other",
    "label": "Other — سایر",
    "fa": "سایر",
    "avgPricePerSqm": 2891923
  },
  {
    "value": "Ozgol",
    "label": "Ozgol — ازگل",
    "fa": "ازگل",
    "avgPricePerSqm": 7076708
  },
  {
    "value": "Park Shahr",
    "label": "Park Shahr — پارک شهر",
    "fa": "پارک شهر",
    "avgPricePerSqm": 3250800
  },
  {
    "value": "Pasdar Gomnam",
    "label": "Pasdar Gomnam — پاسدار گمنام",
    "fa": "پاسدار گمنام",
    "avgPricePerSqm": 3002337
  },
  {
    "value": "Pasdaran",
    "label": "Pasdaran — پاسداران",
    "fa": "پاسداران",
    "avgPricePerSqm": 8850424
  },
  {
    "value": "Pasteur",
    "label": "Pasteur — پاستور",
    "fa": "پاستور",
    "avgPricePerSqm": 3637811
  },
  {
    "value": "Pedar Sani",
    "label": "Pedar Sani — پدرثانی",
    "fa": "پدرثانی",
    "avgPricePerSqm": 3750000
  },
  {
    "value": "Persian Gulf Boulevard",
    "label": "Persian Gulf Boulevard — بلوار خلیج فارس",
    "fa": "بلوار خلیج فارس",
    "avgPricePerSqm": 2182216
  },
  {
    "value": "Piche Shemran",
    "label": "Piche Shemran — پیچ شمیران",
    "fa": "پیچ شمیران",
    "avgPricePerSqm": 3747623
  },
  {
    "value": "Piroozi",
    "label": "Piroozi — پیروزی",
    "fa": "پیروزی",
    "avgPricePerSqm": 3265516
  },
  {
    "value": "Pol-e Choubi",
    "label": "Pol-e Choubi — پل چوبی",
    "fa": "پل چوبی",
    "avgPricePerSqm": 3286118
  },
  {
    "value": "Pol-e Siman",
    "label": "Pol-e Siman — پل سیمان",
    "fa": "پل سیمان",
    "avgPricePerSqm": 2191111
  },
  {
    "value": "Police",
    "label": "Police — پلیس",
    "fa": "پلیس",
    "avgPricePerSqm": 4200046
  },
  {
    "value": "Poonak",
    "label": "Poonak — پونک",
    "fa": "پونک",
    "avgPricePerSqm": 5358745
  },
  {
    "value": "Qazvin",
    "label": "Qazvin — قزوین",
    "fa": "قزوین",
    "avgPricePerSqm": 2507468,
    "aliases": [
      "قزوین(از نواب تا سه راه آذری)"
    ]
  },
  {
    "value": "Qazvin Square",
    "label": "Qazvin Square — میدان قزوین",
    "fa": "میدان قزوین",
    "avgPricePerSqm": 2437452
  },
  {
    "value": "Qazvin Street",
    "label": "Qazvin Street — خیابان قزوین",
    "fa": "خیابان قزوین",
    "avgPricePerSqm": 2561000,
    "aliases": [
      "خیابان قزوین(از ولیعصر تا نواب)"
    ]
  },
  {
    "value": "Qiyam Square",
    "label": "Qiyam Square — میدان قیام",
    "fa": "میدان قیام",
    "avgPricePerSqm": 2891933
  },
  {
    "value": "Qom Road",
    "label": "Qom Road — جاده قم",
    "fa": "جاده قم",
    "avgPricePerSqm": 2866667
  },
  {
    "value": "Rah ahan",
    "label": "Rah ahan — شهرک راه آهن",
    "fa": "شهرک راه آهن",
    "avgPricePerSqm": 4314103,
    "aliases": [
      "میدان راه آهن"
    ]
  },
  {
    "value": "Resalat Square",
    "label": "Resalat Square — میدان رسالت",
    "fa": "میدان رسالت",
    "avgPricePerSqm": 4268417
  },
  {
    "value": "Rey",
    "label": "Rey — ری",
    "fa": "ری",
    "avgPricePerSqm": 2726930
  },
  {
    "value": "Rudaki",
    "label": "Rudaki — رودکی",
    "fa": "رودکی",
    "avgPricePerSqm": 2988218,
    "aliases": [
      "رودکی(سلسبیل)"
    ]
  },
  {
    "value": "Saadat Abad",
    "label": "Saadat Abad — سعادت آباد",
    "fa": "سعادت آباد",
    "avgPricePerSqm": 8488522
  },
  {
    "value": "Saadi",
    "label": "Saadi — سعدی",
    "fa": "سعدی",
    "avgPricePerSqm": 3701933
  },
  {
    "value": "Sabalan",
    "label": "Sabalan — سبلان",
    "fa": "سبلان",
    "avgPricePerSqm": 3148395
  },
  {
    "value": "Sadeghieh",
    "label": "Sadeghieh — صادقیه",
    "fa": "صادقیه",
    "avgPricePerSqm": 4716587
  },
  {
    "value": "Saeed Abad",
    "label": "Saeed Abad — سعید آباد",
    "fa": "سعید آباد",
    "avgPricePerSqm": 6333333
  },
  {
    "value": "Sangelaj",
    "label": "Sangelaj — سنگلچ",
    "fa": "سنگلچ",
    "avgPricePerSqm": 2475000
  },
  {
    "value": "Sattari",
    "label": "Sattari — ستاری",
    "fa": "ستاری",
    "avgPricePerSqm": 4825725,
    "aliases": [
      "Sattari (Ab ta Noor)",
      "ستاری (از آب شناسان تا میدان نور)"
    ]
  },
  {
    "value": "Sattarkhan",
    "label": "Sattarkhan — ستارخان",
    "fa": "ستارخان",
    "avgPricePerSqm": 4583824
  },
  {
    "value": "Sepahbod Gharani",
    "label": "Sepahbod Gharani — سپهبد قرنی",
    "fa": "سپهبد قرنی",
    "avgPricePerSqm": 4838885
  },
  {
    "value": "Seraj",
    "label": "Seraj — سراج",
    "fa": "سراج",
    "avgPricePerSqm": 3500947
  },
  {
    "value": "Seul",
    "label": "Seul — سئول",
    "fa": "سئول",
    "avgPricePerSqm": 6808950
  },
  {
    "value": "Seyed Khandan",
    "label": "Seyed Khandan — سید خندان",
    "fa": "سید خندان",
    "avgPricePerSqm": 5087765
  },
  {
    "value": "Shad Abad",
    "label": "Shad Abad — شاد آباد",
    "fa": "شاد آباد",
    "avgPricePerSqm": 2205815
  },
  {
    "value": "Shahid Kazemi",
    "label": "Shahid Kazemi — شهید کاظمی",
    "fa": "شهید کاظمی",
    "avgPricePerSqm": 1981250
  },
  {
    "value": "Shahid Rajaei",
    "label": "Shahid Rajaei — شهید رجایی",
    "fa": "شهید رجایی",
    "avgPricePerSqm": 2489167,
    "aliases": [
      "شهید رجایی(از شوش تا آزادگان)"
    ]
  },
  {
    "value": "Shahr Ara",
    "label": "Shahr Ara — شهرآرا",
    "fa": "شهرآرا",
    "avgPricePerSqm": 5347763
  },
  {
    "value": "Shahr Ziba",
    "label": "Shahr Ziba — شهرزیبا",
    "fa": "شهرزیبا",
    "avgPricePerSqm": 4202260
  },
  {
    "value": "Shahr-e Rey",
    "label": "Shahr-e Rey — شهر ری",
    "fa": "شهر ری",
    "avgPricePerSqm": 2457149
  },
  {
    "value": "Shahrak Gharb",
    "label": "Shahrak Gharb — شهرک غرب",
    "fa": "شهرک غرب",
    "avgPricePerSqm": 9593639
  },
  {
    "value": "Shahran",
    "label": "Shahran — شهران",
    "fa": "شهران",
    "avgPricePerSqm": 4635094
  },
  {
    "value": "Shams Abad",
    "label": "Shams Abad — شمس آباد",
    "fa": "شمس آباد",
    "avgPricePerSqm": 5357283
  },
  {
    "value": "Shamshiri",
    "label": "Shamshiri — شمشیری",
    "fa": "شمشیری",
    "avgPricePerSqm": 2700202
  },
  {
    "value": "Shariati",
    "label": "Shariati — شریعتی",
    "fa": "شریعتی",
    "avgPricePerSqm": 6097724,
    "aliases": [
      "Shariati (Shiraz-Shemran)",
      "شریعتی( ازهمت تا بهارشیراز)",
      "شریعتی(از Tajrish تا پل صدر)",
      "شریعتی(از بهار شیراز تا پیچ شمیران)",
      "شریعتی(از تجریش تا پل صدر)",
      "شریعتی(از صدر تا همت)"
    ]
  },
  {
    "value": "Sheikh Bahaii",
    "label": "Sheikh Bahaii — شیخ بهایی",
    "fa": "شیخ بهایی",
    "avgPricePerSqm": 9012608
  },
  {
    "value": "Shoush",
    "label": "Shoush — شوش",
    "fa": "شوش",
    "avgPricePerSqm": 2004778
  },
  {
    "value": "Sohanank",
    "label": "Sohanank — سوهانک",
    "fa": "سوهانک",
    "avgPricePerSqm": 6656531
  },
  {
    "value": "Sohrevardi J",
    "label": "Sohrevardi J — سهروردی جنوبی",
    "fa": "سهروردی جنوبی",
    "avgPricePerSqm": 5298366
  },
  {
    "value": "Sohrevardi Shomali",
    "label": "Sohrevardi Shomali — سهروردی شمالی",
    "fa": "سهروردی شمالی",
    "avgPricePerSqm": 6595823
  },
  {
    "value": "Soleimanieh",
    "label": "Soleimanieh — سلیمانیه",
    "fa": "سلیمانیه",
    "avgPricePerSqm": 2907143
  },
  {
    "value": "South 10th Farvardin",
    "label": "South 10th Farvardin — دهم فروردین جنوبی",
    "fa": "دهم فروردین جنوبی",
    "avgPricePerSqm": 3108750
  },
  {
    "value": "South Abuzar Boulevard",
    "label": "South Abuzar Boulevard — بلوار ابوذر جنوبی",
    "fa": "بلوار ابوذر جنوبی",
    "avgPricePerSqm": 3112035
  },
  {
    "value": "South Kargar",
    "label": "South Kargar — کارگر جنوبی",
    "fa": "کارگر جنوبی",
    "avgPricePerSqm": 2984266
  },
  {
    "value": "South Nabard",
    "label": "South Nabard — نبرد جنوبی",
    "fa": "نبرد جنوبی",
    "avgPricePerSqm": 3148655
  },
  {
    "value": "Taghi Abad",
    "label": "Taghi Abad — تقی آباد",
    "fa": "تقی آباد",
    "avgPricePerSqm": 1280000
  },
  {
    "value": "Tajrish",
    "label": "Tajrish — تجریش",
    "fa": "تجریش",
    "avgPricePerSqm": 10087914
  },
  {
    "value": "Taleghani",
    "label": "Taleghani — طالقانی",
    "fa": "طالقانی",
    "avgPricePerSqm": 4259821
  },
  {
    "value": "Tarasht",
    "label": "Tarasht — طرشت",
    "fa": "طرشت",
    "avgPricePerSqm": 4088465
  },
  {
    "value": "Tavanir",
    "label": "Tavanir — توانیر",
    "fa": "توانیر",
    "avgPricePerSqm": 8157385
  },
  {
    "value": "Tehran No",
    "label": "Tehran No — تهران نو",
    "fa": "تهران نو",
    "avgPricePerSqm": 3721106
  },
  {
    "value": "Tehran Sar",
    "label": "Tehran Sar — تهرانسر",
    "fa": "تهرانسر",
    "avgPricePerSqm": 3238041
  },
  {
    "value": "Tehran Vila",
    "label": "Tehran Vila — تهران ویلا",
    "fa": "تهران ویلا",
    "avgPricePerSqm": 5383510
  },
  {
    "value": "Tehranpars",
    "label": "Tehranpars — تهران پارس",
    "fa": "تهران پارس",
    "avgPricePerSqm": 4235878
  },
  {
    "value": "Tondguyan",
    "label": "Tondguyan — تندگویان",
    "fa": "تندگویان",
    "avgPricePerSqm": 3150000
  },
  {
    "value": "Vahdat Eslami",
    "label": "Vahdat Eslami — وحدت اسلامی",
    "fa": "وحدت اسلامی",
    "avgPricePerSqm": 2586079
  },
  {
    "value": "Vahidieh",
    "label": "Vahidieh — وحیدیه",
    "fa": "وحیدیه",
    "avgPricePerSqm": 3171204
  },
  {
    "value": "Valiasr",
    "label": "Valiasr — ولیعصر",
    "fa": "ولیعصر",
    "avgPricePerSqm": 5831533,
    "aliases": [
      "Valiasr (Hemmat - Enghelab)",
      "Valiasr (Park way)",
      "ولیعصر (از پارک وی تا تجریش)",
      "ولیعصر( از همت تا خیابان انقلاب)",
      "ولیعصر( از ونک تا پارک وی)",
      "ولیعصر(از چهارراه تا راه آهن)"
    ]
  },
  {
    "value": "Vanak",
    "label": "Vanak — ونک",
    "fa": "ونک",
    "avgPricePerSqm": 7970284
  },
  {
    "value": "Varamin Junction",
    "label": "Varamin Junction — سه راه ورامین",
    "fa": "سه راه ورامین",
    "avgPricePerSqm": 2500000
  },
  {
    "value": "Vardavard",
    "label": "Vardavard — وردآورد",
    "fa": "وردآورد",
    "avgPricePerSqm": 2568221
  },
  {
    "value": "Velenjak",
    "label": "Velenjak — ولنجک",
    "fa": "ولنجک",
    "avgPricePerSqm": 13344288
  },
  {
    "value": "Vila Shahr",
    "label": "Vila Shahr — ویلا شهر",
    "fa": "ویلا شهر",
    "avgPricePerSqm": 3214545
  },
  {
    "value": "Vozara",
    "label": "Vozara — وزراء",
    "fa": "وزراء",
    "avgPricePerSqm": 6336682
  },
  {
    "value": "Yaft Abad",
    "label": "Yaft Abad — یافت آباد",
    "fa": "یافت آباد",
    "avgPricePerSqm": 2230124
  },
  {
    "value": "Yakhchi Abad",
    "label": "Yakhchi Abad — یاخچی آباد",
    "fa": "یاخچی آباد",
    "avgPricePerSqm": 2672429
  },
  {
    "value": "Yousef Abad",
    "label": "Yousef Abad — یوسف آباد",
    "fa": "یوسف آباد",
    "avgPricePerSqm": 7159842
  },
  {
    "value": "Zafar",
    "label": "Zafar — ظفر",
    "fa": "ظفر",
    "avgPricePerSqm": 7387379
  },
  {
    "value": "Zaferanieh",
    "label": "Zaferanieh — زعفرانیه",
    "fa": "زعفرانیه",
    "avgPricePerSqm": 14579986
  },
  {
    "value": "Zamzam",
    "label": "Zamzam — زمزم",
    "fa": "زمزم",
    "avgPricePerSqm": 2293000
  },
  {
    "value": "Zanjan",
    "label": "Zanjan — زنجان",
    "fa": "زنجان",
    "avgPricePerSqm": 3703267
  }
];

const FALLBACK_DEMO_ACCOUNTS = [
  {
    id: "admin-demo",
    user_id: null,
    displayName: "Admin Demo",
    email: "admin@housing-ai.demo",
    role: "admin",
    roleLabel: "System Admin",
    accessLabel: "Full platform access",
    projectIds: null,
    projectNames: [],
  },
  {
    id: "owner-demo", user_id: 91, displayName: "Owner Demo", email: "owner@housing-ai.demo", phone_number: "09123456789",
    role: "project_owner", roleLabel: "Project Owner", accessLabel: "Assigned project access", projectIds: ["1"], projectNames: ["Aria Residences"], username: "owner",
  },
  {
    id: "member-demo", user_id: 1, displayName: "Member Demo", email: "member@housing-ai.demo", phone_number: "09123456789",
    role: "MEMBER", roleLabel: "Member", accessLabel: "Find projects and manage payments", projectIds: [], projectNames: [], username: "member",
  },
];

function normalizeDemoAccount(account) {
  if (!account || !account.id) return null;

  const projectIds = Array.isArray(account.projectIds)
    ? account.projectIds.map(String)
    : account.projectIds === null
      ? null
      : [];

  const projectNames = Array.isArray(account.projectNames)
    ? account.projectNames.filter(Boolean)
    : [];

  return {
    id: String(account.id),
    user_id: account.user_id ?? null,
    displayName: account.displayName || account.full_name || "Demo User",
    email: account.email || "demo@housing-ai.local",
    phone_number: account.phone_number || account.phoneNumber || "",
    role: account.role || "project_owner",
    roleLabel: account.roleLabel || (account.role === "admin" ? "System Admin" : "Project Owner"),
    accessLabel:
      account.accessLabel ||
      (projectNames.length > 0 ? projectNames.join(", ") : "Assigned project access"),
    projectIds,
    projectNames,
    username: account.username || getDemoUsername({
      displayName: account.displayName || account.full_name,
      email: account.email,
      role: account.role,
    }),
  };
}

function normalizeDemoAccounts(accounts) {
  const normalizedAccounts = getArrayFromResponse(accounts)
    .map(normalizeDemoAccount)
    .filter(Boolean);

  return normalizedAccounts.length > 0 ? normalizedAccounts : FALLBACK_DEMO_ACCOUNTS;
}

function normalizeLoginValue(value) {
  return String(value || "").trim().toLowerCase();
}

function getDemoUsername(account) {
  if (!account) return "";
  if (account.role === "admin") return "admin";

  const firstName = String(account.displayName || "")
    .trim()
    .split(/\s+/)[0]
    .toLowerCase();

  if (firstName) return firstName;

  return String(account.email || "")
    .split("@")[0]
    .split(".")[0]
    .toLowerCase();
}

function getDemoPassword(account) {
  return account?.role === "admin" ? "admin" : "1234";
}

function findDemoAccountByLogin(accounts, username, password) {
  const normalizedUsername = normalizeLoginValue(username);
  const normalizedPassword = normalizeLoginValue(password);

  return accounts.find((account) => {
    return (
      getDemoUsername(account) === normalizedUsername &&
      getDemoPassword(account) === normalizedPassword
    );
  }) || null;
}

function getStoredDemoAccount(accounts = FALLBACK_DEMO_ACCOUNTS) {
  try {
    const storedId = localStorage.getItem("housing_ai_demo_account");
    return accounts.find((account) => account.id === storedId) || null;
  } catch {
    return null;
  }
}

function isAdminAccount(account) {
  return account?.role === "admin";
}

function isMemberAccount(account) {
  return ["member", "MEMBER", "buyer"].includes(account?.role);
}

function canAccessProject(project, account) {
  if (!account || isAdminAccount(account)) return true;

  const projectId = String(project?.id ?? project?.project_id ?? "");
  const projectName = String(project?.name || "").trim();

  const idMatch = Array.isArray(account.projectIds)
    ? account.projectIds.map(String).includes(projectId)
    : false;

  const nameMatch = Array.isArray(account.projectNames)
    ? account.projectNames.includes(projectName)
    : false;

  return idMatch || nameMatch;
}

function filterProjectsByAccount(projects, account) {
  return projects.filter((project) => canAccessProject(project, account));
}

function getScopedProjectIdSet(projects, account) {
  return new Set(
    filterProjectsByAccount(projects, account).map((project) => String(project.id))
  );
}

function filterParticipantsByAccount(participants, account, projects) {
  if (!account || isAdminAccount(account)) return participants;

  const projectIds = getScopedProjectIdSet(projects, account);
  return participants.filter((participant) =>
    projectIds.has(String(participant.project_id))
  );
}

function filterPaymentsByAccount(payments, account, projects) {
  if (!account || isAdminAccount(account)) return payments;

  const projectIds = getScopedProjectIdSet(projects, account);
  return payments.filter((payment) => projectIds.has(String(payment.project_id)));
}

function getUsersForParticipants(users, participants) {
  const userIds = new Set(participants.map((participant) => String(participant.user_id)));
  return users.filter((user) => userIds.has(String(user.id)));
}


function getArrayFromResponse(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.data)) return data.data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "-";

  if (typeof value === "number") {
    if (!Number.isFinite(value)) return "-";

    const absValue = Math.abs(value);

    if (Number.isInteger(value) || absValue >= 1000) {
      return Math.round(value).toLocaleString();
    }

    return value.toLocaleString(undefined, {
      maximumFractionDigits: 2,
      minimumFractionDigits: 0,
    });
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (Array.isArray(value)) {
    return value.join(", ");
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}

function formatRiskPercent(value) {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) return "-";

  const boundedValue = Math.max(0, Math.min(100, numericValue));
  return `${Math.round(boundedValue)}%`;
}

function formatCompactAmount(value) {
  if (value === null || value === undefined || value === "") return "-";

  const numberValue = Number(value);
  if (!Number.isFinite(numberValue)) return formatValue(value);

  const absValue = Math.abs(numberValue);

  if (absValue >= 1_000_000_000) {
    return `${(numberValue / 1_000_000_000).toLocaleString(undefined, {
      maximumFractionDigits: 2,
      minimumFractionDigits: 0,
    })}B`;
  }

  if (absValue >= 1_000_000) {
    return `${(numberValue / 1_000_000).toLocaleString(undefined, {
      maximumFractionDigits: 2,
      minimumFractionDigits: 0,
    })}M`;
  }

  if (absValue >= 1_000) {
    return `${(numberValue / 1_000).toLocaleString(undefined, {
      maximumFractionDigits: 1,
      minimumFractionDigits: 0,
    })}K`;
  }

  return formatValue(numberValue);
}



function calculateProjectHorizonMonths(project) {
  if (!project?.expected_end_date) return 12;

  const endDate = new Date(`${project.expected_end_date}T00:00:00`);
  if (Number.isNaN(endDate.getTime())) return 12;

  const today = new Date();
  let months =
    (endDate.getFullYear() - today.getFullYear()) * 12 +
    (endDate.getMonth() - today.getMonth());

  if (endDate.getDate() >= today.getDate()) {
    months += 1;
  }

  return Math.max(1, Math.min(months, 60));
}

function parseDateValue(value) {
  if (!value) return null;

  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatDateValue(value) {
  if (!value) return "-";
  const date = parseDateValue(value);
  if (!date) return formatValue(value);

  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });
}

function daysBetweenDates(startValue, endValue) {
  const start = parseDateValue(startValue);
  const end = parseDateValue(endValue);

  if (!start || !end) return null;

  const diffMs = end.getTime() - start.getTime();
  return Math.round(diffMs / (1000 * 60 * 60 * 24));
}

function formatIntervalDays(days) {
  if (days === null || days === undefined || !Number.isFinite(Number(days))) {
    return "first round";
  }

  const value = Math.abs(Number(days));

  if (value >= 27 && value <= 33) return "about 1 month";
  if (value >= 80 && value <= 100) return "about 3 months";
  if (value >= 170 && value <= 190) return "about 6 months";
  if (value >= 350 && value <= 380) return "about 1 year";

  return `${Math.round(value)} days`;
}

function summarizePaymentSeries(payments = []) {
  const validPayments = payments.filter((payment) =>
    payment?.due_date && ["installment", "cost_share"].includes(String(payment.payment_type || "installment").toLowerCase())
  );

  if (!validPayments.length) {
    return {
      totalRounds: 0,
      firstDueDate: null,
      lastDueDate: null,
      averageIntervalDays: null,
      rounds: [],
    };
  }

  const groupedByDueDate = validPayments.reduce((groups, payment) => {
    const dueDate = String(payment.due_date || "").slice(0, 10);

    if (!groups[dueDate]) {
      groups[dueDate] = [];
    }

    groups[dueDate].push(payment);
    return groups;
  }, {});

  const dueDates = Object.keys(groupedByDueDate).sort();

  const rounds = dueDates.map((dueDate, index) => {
    const roundPayments = groupedByDueDate[dueDate];
    const previousDueDate = dueDates[index - 1] || null;
    const intervalDays = previousDueDate ? daysBetweenDates(previousDueDate, dueDate) : null;
    const paidDates = roundPayments
      .map((payment) => payment.paid_date)
      .filter(Boolean)
      .sort();

    const statusCounts = roundPayments.reduce((counts, payment) => {
      const status = String(payment.status || "unknown").toLowerCase();
      counts[status] = (counts[status] || 0) + 1;
      return counts;
    }, {});

    return {
      roundNumber: index + 1,
      dueDate,
      intervalDays,
      intervalLabel: formatIntervalDays(intervalDays),
      paymentCount: roundPayments.length,
      totalScheduledAmount: roundPayments.reduce((sum, payment) => sum + Number(payment.amount || 0), 0),
      paidAmount: roundPayments
        .filter((payment) => ["paid", "paid_late"].includes(String(payment.status || "").toLowerCase()))
        .reduce((sum, payment) => sum + Number(payment.amount || 0), 0),
      firstPaidDate: paidDates[0] || null,
      lastPaidDate: paidDates[paidDates.length - 1] || null,
      statusCounts,
    };
  });

  const intervals = rounds
    .map((round) => round.intervalDays)
    .filter((value) => Number.isFinite(Number(value)));

  const averageIntervalDays = intervals.length
    ? intervals.reduce((sum, value) => sum + Number(value), 0) / intervals.length
    : null;

  return {
    totalRounds: rounds.length,
    firstDueDate: rounds[0]?.dueDate || null,
    lastDueDate: rounds[rounds.length - 1]?.dueDate || null,
    averageIntervalDays,
    rounds,
  };
}


function PaymentScheduleAnalysis({
  projects = [],
  selectedProjectId,
  onProjectChange,
  paymentSeriesSummary,
  showProjectPicker = false,
}) {
  return (
    <div className="payment-schedule-panel" style={styles.paymentSeriesPanel}>
      <div style={styles.paymentSeriesHeader}>
        <div>
          <p style={styles.controlEyebrow}>Payment schedule analysis</p>
          <h3 style={styles.paymentSeriesTitle}>Payment rounds</h3>
        </div>
        <span style={styles.scopeBadgeMuted}>
          {paymentSeriesSummary.totalRounds} round{paymentSeriesSummary.totalRounds === 1 ? "" : "s"}
        </span>
      </div>

      {showProjectPicker && (
        <div style={{ marginBottom: "14px" }}>
          <label style={styles.label}>Project</label>
          <DownwardDropdown
            value={selectedProjectId}
            onChange={onProjectChange}
            options={projects.map((project) => ({
              value: String(project.id),
              label: project.name,
            }))}
            placeholder="Select project"
          />
        </div>
      )}

      {paymentSeriesSummary.totalRounds === 0 ? (
        <p style={styles.scopeDescription}>No scheduled payments found for this project yet.</p>
      ) : (
        <>
          <div style={styles.resultMetricGrid}>
            <div className="result-metric" style={styles.resultMetric}>
              <span>Total rounds</span>
              <strong>{formatValue(paymentSeriesSummary.totalRounds)}</strong>
            </div>
            <div className="result-metric" style={styles.resultMetric}>
              <span>First due date</span>
              <strong>{formatDateValue(paymentSeriesSummary.firstDueDate)}</strong>
            </div>
            <div className="result-metric" style={styles.resultMetric}>
              <span>Last due date</span>
              <strong>{formatDateValue(paymentSeriesSummary.lastDueDate)}</strong>
            </div>
            <div className="result-metric" style={styles.resultMetric}>
              <span>Average interval</span>
              <strong>{formatIntervalDays(paymentSeriesSummary.averageIntervalDays)}</strong>
            </div>
          </div>

          <div style={styles.paymentSeriesTable}>
            {paymentSeriesSummary.rounds.map((round) => (
              <div key={round.dueDate} style={styles.paymentSeriesRow}>
                <strong>Round {round.roundNumber}</strong>
                <span>Due: {formatDateValue(round.dueDate)}</span>
                <span>Interval: {round.intervalLabel}</span>
                <span>{round.paymentCount} payment{round.paymentCount === 1 ? "" : "s"}</span>
                <span>Scheduled: {formatCompactAmount(round.totalScheduledAmount)}</span>
                <span>Paid: {formatCompactAmount(round.paidAmount)}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function getPaymentProjectKey(payment) {
  return String(
    payment.project_id ??
      payment.projectId ??
      payment.project?.id ??
      payment.project_name ??
      payment.projectName ??
      ""
  ).trim();
}

function getProjectPaymentSummary(project, payments = []) {
  const projectId = String(project?.id ?? "").trim();
  const projectName = String(project?.name ?? "").trim();

  const projectPayments = payments.filter((payment) => {
    const key = getPaymentProjectKey(payment);
    return key === projectId || key === projectName;
  });

  const isPenalty = (payment) =>
    String(payment.payment_type || payment.paymentType || "").toLowerCase() === "penalty";

  const collectedAmount = projectPayments
    .filter(
      (payment) =>
        !isPenalty(payment) &&
        ["paid", "paid_late"].includes(String(payment.status || "").toLowerCase()),
    )
    .reduce((sum, payment) => sum + Number(payment.amount || 0), 0);

  const feeCollectedAmount = projectPayments
    .filter(
      (payment) =>
        isPenalty(payment) &&
        ["paid", "paid_late"].includes(String(payment.status || "").toLowerCase()),
    )
    .reduce((sum, payment) => sum + Number(payment.amount || 0), 0);

  const overdueAmount = projectPayments
    .filter(
      (payment) =>
        !isPenalty(payment) &&
        String(payment.status || "").toLowerCase() === "overdue",
    )
    .reduce(
      (sum, payment) =>
        sum + Number(payment.amount || 0) + Number(payment.accrued_penalty_amount || 0),
      0,
    );

  const unpaidAmount = projectPayments
    .filter(
      (payment) =>
        !isPenalty(payment) &&
        String(payment.status || "").toLowerCase() === "unpaid",
    )
    .reduce((sum, payment) => sum + Number(payment.amount || 0), 0);

  const remainingAmount = overdueAmount + unpaidAmount;
  const scheduledAmount = collectedAmount + remainingAmount;
  const backendProgress = Number(project?.payment_progress ?? project?.progress);
  const progress = Number.isFinite(backendProgress)
    ? backendProgress
    : scheduledAmount > 0
    ? (collectedAmount / scheduledAmount) * 100
    : 0;

  return {
    collectedAmount,
    feeCollectedAmount,
    overdueAmount,
    unpaidAmount,
    remainingAmount,
    scheduledAmount,
    progress,
  };
}

function cleanText(value) {
  const cleaned = String(value || "").trim();
  return cleaned === "" ? null : cleaned;
}

function cleanNumber(value) {
  if (value === null || value === undefined || value === "") return null;

  const numberValue = Number(String(value).replace(/,/g, ""));
  return Number.isNaN(numberValue) ? null : numberValue;
}

function formatThousands(value) {
  const digits = String(value ?? "").replace(/\D/g, "");
  return digits.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function Sidebar({ collapsed, onToggle, currentAccount, onSwitchAccount }) {
  const links = isMemberAccount(currentAccount)
    ? [{ to: "/member", label: "Member dashboard", icon: UsersRound }]
    : [
      { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { to: "/projects", label: isAdminAccount(currentAccount) ? "Projects" : "My Projects", icon: Building2 },
      { to: "/users", label: isAdminAccount(currentAccount) ? "Users" : "Members", icon: UsersRound },
      { to: "/payments", label: "Payments", icon: CreditCard },
      { to: "/predictions", label: "Predictions", icon: Sparkles },
      ...(!isAdminAccount(currentAccount) ? [{ to: "/membership-requests", label: "Membership Requests", icon: UsersRound }] : []),
    ];

  const sidebarStyle = {
    width: collapsed ? "88px" : "250px",
    height: "100vh",
    minHeight: "100vh",
    position: "sticky",
    top: 0,
    backgroundColor: "#121a22",
    color: "#ffffff",
    padding: collapsed ? "24px 14px" : "24px 18px",
    boxSizing: "border-box",
    transition: "all 0.25s ease",
    flexShrink: 0,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    zIndex: 20,
  };

  const headerStyle = {
    display: "flex",
    alignItems: "center",
    justifyContent: collapsed ? "center" : "space-between",
    gap: "10px",
    marginBottom: "32px",
  };

  const logoStyle = {
    fontSize: collapsed ? "20px" : "22px",
    margin: 0,
    whiteSpace: "nowrap",
  };

  const toggleStyle = {
    width: "36px",
    height: "36px",
    border: "1px solid rgba(255,255,255,0.18)",
    borderRadius: "10px",
    backgroundColor: "rgba(255,255,255,0.1)",
    color: "#ffffff",
    cursor: "pointer",
    fontSize: "18px",
  };

  const navStyle = {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    flex: 1,
  };

  const iconStyle = {
    width: "30px",
    height: "30px",
    borderRadius: "9px",
    backgroundColor: "rgba(255,255,255,0.1)",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "12px",
    fontWeight: 800,
    flexShrink: 0,
  };

  return (
    <aside className="presentation-sidebar" style={sidebarStyle}>
      <div style={headerStyle}>
        {!collapsed && (
          <div className="presentation-brand">
            <span><Building2 size={19} strokeWidth={1.9} /></span>
            <h2 style={logoStyle}>Housing AI</h2>
          </div>
        )}

        {collapsed && <span className="presentation-brand-mark"><Building2 size={20} strokeWidth={1.9} /></span>}

        <button
          type="button"
          onClick={onToggle}
          style={toggleStyle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}
        </button>
      </div>

      <nav style={navStyle}>
        {links.map((link) => {
          const Icon = link.icon;
          return (
          <NavLink
            key={link.to}
            to={link.to}
            title={link.label}
            style={({ isActive }) => ({
              color: "#cbd2df",
              textDecoration: "none",
              padding: collapsed ? "12px 8px" : "12px 14px",
              borderRadius: "10px",
              fontSize: "15px",
              display: "flex",
              alignItems: "center",
              justifyContent: collapsed ? "center" : "flex-start",
              gap: "10px",
              minHeight: "44px",
              boxSizing: "border-box",
              backgroundColor: isActive ? "#4f7188" : "transparent",
            })}
          >
            <span style={iconStyle}><Icon size={17} strokeWidth={1.8} /></span>
            {!collapsed && <span>{link.label}</span>}
          </NavLink>
          );
        })}
      </nav>

      {!collapsed && currentAccount && (
        <div style={styles.sidebarAccountCard}>
          <span style={styles.sidebarAccountRole}>{currentAccount.roleLabel}</span>
          <strong style={styles.sidebarAccountName}>{currentAccount.displayName}</strong>
          <p style={styles.sidebarAccountText}>{currentAccount.accessLabel}</p>
          <button type="button" onClick={onSwitchAccount} style={styles.sidebarAccountButton}>
            Switch account
          </button>
        </div>
      )}

      {collapsed && currentAccount && (
        <button
          type="button"
          onClick={onSwitchAccount}
          title={`Switch account: ${currentAccount.displayName}`}
          style={styles.sidebarCollapsedAccount}
        >
          {isAdminAccount(currentAccount) ? "AD" : isMemberAccount(currentAccount) ? "MB" : "OW"}
        </button>
      )}
    </aside>
  );
}

function PageTitle({ title, subtitle }) {
  return (
    <div className="presentation-page-title" style={styles.pageTitle}>
      <h1 style={styles.h1}>{title}</h1>
      {subtitle && <p style={styles.subtitle}>{subtitle}</p>}
    </div>
  );
}

function AppTopbar({ currentAccount }) {
  const location = useLocation();
  const pageLabels = {
    "/dashboard": "Dashboard",
    "/projects": isAdminAccount(currentAccount) ? "Projects" : "My Projects",
    "/users": isAdminAccount(currentAccount) ? "Users" : "Members",
    "/payments": "Payments",
    "/predictions": "Predictions",
  };
  const pageLabel = pageLabels[location.pathname] || "Workspace";
  const initials = String(currentAccount?.displayName || "User")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

  return (
    <header className="presentation-topbar">
      <div className="presentation-breadcrumb">
        <span className="presentation-topbar-mark"><HardHat size={17} strokeWidth={1.8} /></span>
        <span>Project operations</span>
        <ChevronRight size={14} />
        <strong>{pageLabel}</strong>
      </div>

      <div className="presentation-account-summary">
        <div className="presentation-account-copy">
          <span>{currentAccount?.roleLabel || "Account"}</span>
          <strong>{currentAccount?.displayName || "User"}</strong>
        </div>
        <span className="presentation-account-avatar">{initials || "U"}</span>
      </div>
    </header>
  );
}

function LoadingBox() {
  return <div className="state-box state-loading" style={styles.infoBox}><span />Loading data...</div>;
}

function ErrorBox({ message }) {
  return (
    <div className="state-box state-error" style={styles.errorBox}>
      <strong>Error:</strong> {message}
    </div>
  );
}

function SuccessBox({ message }) {
  return (
    <div className="state-box state-success" style={styles.successBox}>
      <strong>Success:</strong> {message}
    </div>
  );
}

function EmptyBox({ message }) {
  return <div className="state-box state-empty" style={styles.infoBox}>{message}</div>;
}

function StatusBadge({ value }) {
  const status = String(value || "").toLowerCase();

  let badgeStyle = styles.badgeDefault;
  let badgeVariant = "default";

  if (status === "paid" || status === "low" || status === "completed") {
    badgeStyle = styles.badgeGreen;
    badgeVariant = "success";
  }

  if (
    status === "paid_late" ||
    status === "medium" ||
    status === "planning" ||
    status === "unpaid"
  ) {
    badgeStyle = styles.badgeYellow;
    badgeVariant = "warning";
  }

  if (status === "overdue" || status === "high" || status === "delayed") {
    badgeStyle = styles.badgeRed;
    badgeVariant = "danger";
  }

  if (status === "critical") {
    badgeStyle = styles.badgePurple;
    badgeVariant = "critical";
  }

  return <span className={`status-badge status-badge-${badgeVariant}`} style={{ ...styles.badge, ...badgeStyle }}>{formatValue(value)}</span>;
}

function DownwardDropdown({ value, onChange, options, placeholder = "Select option" }) {
  const [open, setOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [panelPosition, setPanelPosition] = useState({ left: 0, top: 0, width: 0 });
  const dropdownRef = useRef(null);
  const panelRef = useRef(null);

  const selectedOption = options.find((option) => String(option.value) === String(value));
  const searchable = options.length > 20;
  const normalizedSearch = searchTerm.trim().toLowerCase();
  const filteredOptions = normalizedSearch
    ? options.filter((option) => {
        const searchTarget = [
          option.label,
          option.value,
          option.fa,
          ...(option.aliases || []),
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();

        return searchTarget.includes(normalizedSearch);
      })
    : options;

  function updatePanelPosition() {
    if (!dropdownRef.current) return;

    const rect = dropdownRef.current.getBoundingClientRect();
    setPanelPosition({
      left: rect.left,
      top: rect.bottom + 8,
      width: rect.width,
    });
  }

  useEffect(() => {
    function handleDocumentClick(event) {
      const clickedButton = dropdownRef.current?.contains(event.target);
      const clickedPanel = panelRef.current?.contains(event.target);

      if (!clickedButton && !clickedPanel) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleDocumentClick);
    return () => document.removeEventListener("mousedown", handleDocumentClick);
  }, []);

  useEffect(() => {
    if (!open) {
      setSearchTerm("");
      return undefined;
    }

    updatePanelPosition();

    window.addEventListener("resize", updatePanelPosition);
    window.addEventListener("scroll", updatePanelPosition, true);

    return () => {
      window.removeEventListener("resize", updatePanelPosition);
      window.removeEventListener("scroll", updatePanelPosition, true);
    };
  }, [open]);

  return (
    <div
      ref={dropdownRef}
      style={styles.dropdownShell}
    >
      <button
        type="button"
        onClick={() => {
          if (!open) updatePanelPosition();
          setOpen((previous) => !previous);
        }}
        style={{
          ...styles.input,
          ...styles.dropdownButton,
          ...(open ? styles.dropdownButtonOpen : {}),
        }}
      >
        <span style={styles.dropdownButtonText}>
          {selectedOption?.label || placeholder}
        </span>
        <span style={{
          ...styles.dropdownChevron,
          transform: open ? "rotate(180deg)" : "rotate(0deg)",
        }}>⌄</span>
      </button>

      {open && createPortal(
        <div
          ref={panelRef}
          className="dropdown-panel"
          style={{
            ...styles.dropdownPanel,
            position: "fixed",
            top: `${panelPosition.top}px`,
            left: `${panelPosition.left}px`,
            right: "auto",
            width: `${panelPosition.width}px`,
            zIndex: 2147483647,
          }}
        >
          {searchable && (
            <div style={styles.dropdownSearchWrap}>
              <input
                type="text"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search neighborhood..."
                autoFocus
                style={styles.dropdownSearchInput}
              />
            </div>
          )}

          {filteredOptions.length === 0 ? (
            <div style={styles.dropdownEmpty}>No matching neighborhood</div>
          ) : (
            filteredOptions.map((option) => {
              const isSelected = String(option.value) === String(value);

              return (
                <button
                  type="button"
                  key={`${option.value}-${option.label}`}
                  onClick={() => {
                    onChange(option.value);
                    setOpen(false);
                  }}
                  style={{
                    ...styles.dropdownOption,
                    ...(isSelected ? styles.dropdownOptionActive : {}),
                  }}
                >
                  <span>{option.label}</span>
                </button>
              );
            })
          )}
        </div>,
        document.body
      )}
    </div>
  );
}

function GlobalUIStyles() {
  return (
    <style>
      {`
        @keyframes appFadeUp {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes softPulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.68; }
        }

        @keyframes smoothPopoverIn {
          from { opacity: 0; transform: translateY(-6px) scale(0.98); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }

        @keyframes smoothModalIn {
          from { opacity: 0; transform: scale(0.98) translateY(8px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }

        @keyframes smoothOverlayIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        .dropdown-panel, .participant-expanded-panel, .participant-hover-panel {
          animation: smoothPopoverIn 0.18s ease both;
          transform-origin: top center;
        }

        .presentation-page-shell > * {
          animation: appFadeUp 0.22s ease both;
        }

        button {
          transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease, background-color 0.18s ease, border-color 0.18s ease;
        }

        button:not(:disabled):hover {
          transform: translateY(-1px);
          filter: brightness(1.03);
        }

        button:not(:disabled):active {
          transform: translateY(0);
        }

        input, select {
          transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
        }

        input:focus, select:focus {
          outline: none;
          border-color: #4f7188 !important;
          box-shadow: 0 0 0 4px rgba(79, 113, 136, 0.12);
        }

        table tbody tr {
          transition: background-color 0.16s ease, transform 0.16s ease;
        }

        table tbody tr:hover {
          background-color: #f7f8fc;
        }

        table thead th {
          position: sticky;
          top: 0;
          z-index: 1;
        }

        .metric-card {
          transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }

        .metric-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 16px 36px rgba(18, 26, 34, 0.10) !important;
          border-color: #c4d0d7 !important;
        }

        .nav-item {
          transition: background-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
        }

        .nav-item:hover {
          transform: translateX(2px);
          background-color: rgba(255,255,255,0.08);
          color: #ffffff !important;
        }

        .live-dot {
          animation: softPulse 1.4s ease-in-out infinite;
        }
      `}
    </style>
  );
}

function GenericTable({ rows, renderActions = null }) {
  if (!rows.length) {
    return <EmptyBox message="No data found." />;
  }

  const columns = Object.keys(rows[0]).slice(0, 10);

  return (
    <div className="presentation-table" style={styles.tableWrapper}>
      <table style={styles.table}>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column} style={styles.th}>
                {column}
              </th>
            ))}
            {renderActions && <th style={styles.th}>Actions</th>}
          </tr>
        </thead>

        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={row.id || row.user_id || row.project_id || rowIndex}>
              {columns.map((column) => (
                <td key={column} style={styles.td}>
                  {column.toLowerCase().includes("status") ||
                  column.toLowerCase().includes("risk") ? (
                    <StatusBadge value={row[column]} />
                  ) : (
                    formatValue(row[column])
                  )}
                </td>
              ))}
              {renderActions && <td style={styles.td}>{renderActions(row)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProjectTable({
  projects,
  payments = [],
  showFinancials = false,
  canDelete = false,
  onDeleteProject,
  deletingProjectId = null,
}) {
  if (!projects.length) {
    return <EmptyBox message="No projects found." />;
  }

  return (
    <div className="presentation-table" style={styles.tableWrapper}>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>ID</th>
            <th style={styles.th}>Project Name</th>
            <th style={styles.th}>Location</th>
            <th style={styles.th}>Status</th>
            <th style={styles.th}>Total Units</th>
            <th style={styles.th}>Estimated Cost</th>
            {showFinancials && <th style={styles.th}>Paid</th>}
            {showFinancials && <th style={styles.th}>Remaining</th>}
            {showFinancials && <th style={styles.th}>Progress</th>}
            <th style={styles.th}>Start Date</th>
            <th style={styles.th}>Expected End Date</th>
            {canDelete && <th style={styles.th}>Actions</th>}
          </tr>
        </thead>

        <tbody>
          {projects.map((project, index) => {
            const paymentSummary = getProjectPaymentSummary(project, payments);

            return (
              <tr key={project.id || index}>
                <td style={styles.td}>{formatValue(project.id)}</td>
                <td style={styles.td}>{formatValue(project.name)}</td>
                <td style={styles.td}>{formatValue(project.location)}</td>
                <td style={styles.td}>
                  <StatusBadge value={project.status} />
                </td>
                <td style={styles.td}>{formatValue(project.total_units)}</td>
                <td style={styles.td}>{formatCompactAmount(project.estimated_total_cost)}</td>
                {showFinancials && (
                  <td style={styles.td}>
                    <strong>{formatCompactAmount(paymentSummary.collectedAmount)}</strong>
                  </td>
                )}
                {showFinancials && (
                  <td style={styles.td}>
                    <strong style={{ color: paymentSummary.remainingAmount > 0 ? "#b45309" : "#15803d" }}>
                      {formatCompactAmount(paymentSummary.remainingAmount)}
                    </strong>
                  </td>
                )}
                {showFinancials && (
                  <td style={styles.td}>
                    <div style={styles.projectProgressCell}>
                      <div style={styles.projectProgressTrack}>
                        <div
                          style={{
                            ...styles.projectProgressFill,
                            width: `${Math.max(0, Math.min(paymentSummary.progress, 100))}%`,
                          }}
                        />
                      </div>
                      <span>{Math.round(paymentSummary.progress)}%</span>
                    </div>
                  </td>
                )}
                <td style={styles.td}>{formatValue(project.start_date)}</td>
                <td style={styles.td}>{formatValue(project.expected_end_date)}</td>
                {canDelete && (
                  <td style={styles.td}>
                    <button
                      type="button"
                      title={`Delete ${project.name || "project"}`}
                      aria-label={`Delete ${project.name || "project"}`}
                      disabled={deletingProjectId === project.id}
                      onClick={() => onDeleteProject?.(project)}
                      style={{
                        ...styles.dangerButton,
                        ...(deletingProjectId === project.id ? styles.disabledButton : {}),
                      }}
                    >
                      <Trash2 size={14} />
                      {deletingProjectId === project.id ? "Deleting..." : "Delete"}
                    </button>
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function PaymentTable({ payments, projects, users }) {
  if (!payments.length) {
    return <EmptyBox message="No payments found." />;
  }

  function getProjectName(projectId) {
    const project = projects.find((item) => String(item.id) === String(projectId));
    return project ? project.name : `Project ${projectId}`;
  }

  function getUserName(userId) {
    const user = users.find((item) => String(item.id) === String(userId));
    return user ? user.full_name : `User ${userId}`;
  }

  return (
    <div className="presentation-table" style={styles.tableWrapper}>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>ID</th>
            <th style={styles.th}>Project</th>
            <th style={styles.th}>User</th>
            <th style={styles.th}>Amount</th>
            <th style={styles.th}>Due Date</th>
            <th style={styles.th}>Paid Date</th>
            <th style={styles.th}>Status</th>
            <th style={styles.th}>Delay Days</th>
            <th style={styles.th}>Accrued Penalty</th>
            <th style={styles.th}>Type</th>
            <th style={styles.th}>Description</th>
          </tr>
        </thead>

        <tbody>
          {payments.map((payment) => (
            <tr key={payment.id}>
              <td style={styles.td}>{formatValue(payment.id)}</td>
              <td style={styles.td}>{getProjectName(payment.project_id)}</td>
              <td style={styles.td}>{getUserName(payment.user_id)}</td>
              <td style={styles.td}>{formatValue(payment.amount)}</td>
              <td style={styles.td}>{formatValue(payment.due_date)}</td>
              <td style={styles.td}>{formatValue(payment.paid_date)}</td>
              <td style={styles.td}>
                <StatusBadge value={payment.status} />
              </td>
              <td style={styles.td}>{formatValue(payment.delay_days)}</td>
              <td style={styles.td}>
                {Number(payment.accrued_penalty_amount || 0) > 0
                  ? formatCompactAmount(payment.accrued_penalty_amount)
                  : "-"}
              </td>
              <td style={styles.td}>{formatValue(payment.payment_type)}</td>
              <td style={styles.td}>{formatValue(payment.description)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      hasError: false,
      errorMessage: "",
    };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      errorMessage: error?.message || "Unknown frontend error",
    };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Frontend render error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={styles.boundaryBox}>
          <h1 style={{ color: "#b91c1c" }}>Frontend Error</h1>
          <p>The page could not render because of a React runtime error.</p>

          <pre style={styles.boundaryPre}>{this.state.errorMessage}</pre>

          <button
            onClick={() =>
              this.setState({
                hasError: false,
                errorMessage: "",
              })
            }
            style={styles.primaryButton}
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}


function LoginScreen({
  accountsLoading,
  accountsError,
  loginError,
  createAccountError,
  creatingAccount,
  onLogin,
  onCreateAccount,
}) {
  const [mode, setMode] = useState("login");
  const [signupRole, setSignupRole] = useState("owner");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [createForm, setCreateForm] = useState({
    full_name: "",
    email: "",
    username: "",
    password: "",
    phone_number: "",
  });

  function handleLoginSubmit(event) {
    event.preventDefault();
    onLogin({ username, password });
  }

  function handleCreateChange(event) {
    const { name, value } = event.target;
    setCreateForm((previous) => ({ ...previous, [name]: value }));
  }

  function handleCreateSubmit(event) {
    event.preventDefault();
    onCreateAccount({
      ...createForm,
      role: signupRole,
    });
  }

  return (
    <div className="presentation-login-page" style={styles.loginPage}>
      <GlobalUIStyles />
      <div className="presentation-login-shell" style={styles.loginShell}>
        <div className="presentation-login-hero" style={styles.loginHeroCard}>
          <p style={styles.controlEyebrow}>Housing AI</p>
          <h1 style={styles.loginTitle}>Build with clarity.</h1>
          <p style={styles.loginSubtitle}>
            Financial control, delivery visibility and project intelligence for modern cooperative housing. Admins manage the full platform; project owners see only their assigned work.
          </p>
          <div className="login-architecture" aria-hidden="true">
            <span className="login-architecture-label">Portfolio intelligence</span>
            <div className="login-building login-building-one"><i /><i /><i /></div>
            <div className="login-building login-building-two"><i /><i /><i /><i /></div>
            <div className="login-building login-building-three"><i /><i /></div>
            <span className="login-ground-line" />
          </div>
        </div>

        <div className="presentation-login-form" style={styles.loginFormCard}>
          <div style={styles.loginTabs}>
            <button
              type="button"
              onClick={() => setMode("login")}
              style={{
                ...styles.loginTabButton,
                ...(mode === "login" ? styles.loginTabButtonActive : {}),
              }}
            >
              Login
            </button>
            <button
              type="button"
              onClick={() => setMode("create")}
              style={{
                ...styles.loginTabButton,
                ...(mode === "create" ? styles.loginTabButtonActive : {}),
              }}
            >
              Create account
            </button>
          </div>

          {mode === "login" ? (
            <form onSubmit={handleLoginSubmit}>
              <span style={styles.loginRolePill}>Secure demo access</span>
              <h2 style={styles.loginFormTitle}>Welcome back</h2>

              {accountsLoading && (
                <div style={styles.loginStatusCard}>Loading accounts from backend...</div>
              )}

              {accountsError && (
                <div style={styles.loginWarningCard}>{accountsError}</div>
              )}

              {loginError && (
                <div style={styles.loginErrorCard}>{loginError}</div>
              )}

              <label style={styles.formGroup}>
                <span style={styles.label}>Username</span>
                <input
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  placeholder="admin, armin, sara..."
                  style={styles.input}
                  autoComplete="username"
                  autoFocus
                />
              </label>

              <label style={styles.formGroup}>
                <span style={styles.label}>Password</span>
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Password"
                  style={styles.input}
                  autoComplete="current-password"
                />
              </label>

              <button
                type="submit"
                style={styles.primaryButton}
                disabled={accountsLoading}
              >
                Login
              </button>
            </form>
          ) : (
            <form onSubmit={handleCreateSubmit}>
              <span style={styles.loginRolePill}>{signupRole === "owner" ? "Project owner" : "Member account"}</span>
              <h2 style={styles.loginFormTitle}>{signupRole === "owner" ? "Create owner account" : "Create member account"}</h2>

              {createAccountError && (
                <div style={styles.loginErrorCard}>{createAccountError}</div>
              )}

              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12,marginBottom:16}}>
                <button type="button" onClick={()=>setSignupRole("owner")} style={{...styles.loginTabButton, ...(signupRole==="owner" ? styles.loginTabButtonActive : {})}}>🏗 Owner</button>
                <button type="button" onClick={()=>setSignupRole("member")} style={{...styles.loginTabButton, ...(signupRole==="member" ? styles.loginTabButtonActive : {})}}>👤 Member</button>
              </div>

              <div style={styles.loginCreateGrid}>
                <label style={styles.formGroup}>
                  <span style={styles.label}>Full name</span>
                  <input
                    name="full_name"
                    value={createForm.full_name}
                    onChange={handleCreateChange}
                    placeholder="Example: Reza Ahmadi"
                    style={styles.input}
                    autoComplete="name"
                  />
                </label>

                <label style={styles.formGroup}>
                  <span style={styles.label}>Email</span>
                  <input
                    name="email"
                    type="email"
                    value={createForm.email}
                    onChange={handleCreateChange}
                    placeholder="owner@example.com"
                    style={styles.input}
                    autoComplete="email"
                  />
                </label>

                <label style={styles.formGroup}>
                  <span style={styles.label}>Username</span>
                  <input
                    name="username"
                    value={createForm.username}
                    onChange={handleCreateChange}
                    placeholder="reza"
                    style={styles.input}
                    autoComplete="username"
                  />
                </label>

                <label style={styles.formGroup}>
                  <span style={styles.label}>Password</span>
                  <input
                    name="password"
                    type="password"
                    value={createForm.password}
                    onChange={handleCreateChange}
                    placeholder="Minimum 3 characters"
                    style={styles.input}
                    autoComplete="new-password"
                  />
                </label>
              </div>

              <label style={{ ...styles.formGroup, marginTop: "12px" }}>
                <span style={styles.label}>Phone number (required)</span>
                <input
                  name="phone_number"
                  value={createForm.phone_number}
                  onChange={handleCreateChange}
                  placeholder="09123456789 or +989123456789"
                  style={styles.input}
                  autoComplete="tel"
                />
              </label>

              <button
                type="submit"
                style={styles.primaryButton}
                disabled={creatingAccount}
              >
                {creatingAccount ? "Creating..." : "Create account"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

function Dashboard({ currentAccount }) {
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [payments, setPayments] = useState([]);
  const [backendStatus, setBackendStatus] = useState("checking");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [deletingProjectId, setDeletingProjectId] = useState(null);

  useEffect(() => {
    Promise.all([
      axios.get(`${API_BASE_URL}/projects/`),
      axios.get(`${API_BASE_URL}/users/`),
      axios.get(`${API_BASE_URL}/participants/`),
      axios.get(`${API_BASE_URL}/payments/`),
    ])
      .then(([projectsResponse, usersResponse, participantsResponse, paymentsResponse]) => {
        setProjects(getArrayFromResponse(projectsResponse.data));
        setUsers(getArrayFromResponse(usersResponse.data));
        setParticipants(getArrayFromResponse(participantsResponse.data));
        setPayments(getArrayFromResponse(paymentsResponse.data));
        setBackendStatus("connected");
      })
      .catch((err) => {
        console.error("Dashboard load error:", err);
        setBackendStatus("disconnected");
        setError(err.message || "Could not connect to backend.");
      });
  }, []);

  const scopedProjects = useMemo(() => {
    return filterProjectsByAccount(projects, currentAccount);
  }, [projects, currentAccount]);

  const scopedParticipants = useMemo(() => {
    return filterParticipantsByAccount(participants, currentAccount, projects);
  }, [participants, currentAccount, projects]);

  const scopedPayments = useMemo(() => {
    return filterPaymentsByAccount(payments, currentAccount, projects);
  }, [payments, currentAccount, projects]);

  const scopedUsers = useMemo(() => {
    return isAdminAccount(currentAccount)
      ? users
      : getUsersForParticipants(users, scopedParticipants);
  }, [users, scopedParticipants, currentAccount]);

  async function handleDeleteProject(project) {
    if (!project?.id || !canAccessProject(project, currentAccount)) return;

    const projectName = project.name || `Project ${project.id}`;
    const confirmed = window.confirm(
      `Delete "${projectName}"? This will permanently remove its payments, expenses, participants, payment plan, and prediction records.`
    );

    if (!confirmed) return;

    setError("");
    setSuccess("");
    setDeletingProjectId(project.id);

    try {
      await axios.delete(`${API_BASE_URL}/projects/${project.id}`);
      setProjects((previous) => previous.filter((item) => String(item.id) !== String(project.id)));
      setPayments((previous) => previous.filter((item) => String(item.project_id) !== String(project.id)));
      setParticipants((previous) => previous.filter((item) => String(item.project_id) !== String(project.id)));
      setSuccess(`Project "${projectName}" deleted successfully.`);
    } catch (err) {
      console.error("Delete project error:", err);
      setError(err.response?.data?.detail || "Could not delete project.");
    } finally {
      setDeletingProjectId(null);
    }
  }

  const isPenaltyPayment = (payment) =>
    String(payment.payment_type || payment.paymentType || "").toLowerCase() === "penalty";

  const collectedAmount = scopedPayments
    .filter(
      (payment) =>
        !isPenaltyPayment(payment) &&
        ["paid", "paid_late"].includes(String(payment.status || "").toLowerCase()),
    )
    .reduce((sum, payment) => sum + Number(payment.amount || 0), 0);

  const overdueAmount = scopedPayments
    .filter(
      (payment) =>
        !isPenaltyPayment(payment) &&
        String(payment.status || "").toLowerCase() === "overdue",
    )
    .reduce(
      (sum, payment) =>
        sum + Number(payment.amount || 0) + Number(payment.accrued_penalty_amount || 0),
      0,
    );

  const unpaidAmount = scopedPayments
    .filter(
      (payment) =>
        !isPenaltyPayment(payment) &&
        String(payment.status || "").toLowerCase() === "unpaid",
    )
    .reduce((sum, payment) => sum + Number(payment.amount || 0), 0);

  const overdueCount = scopedPayments.filter(
    (payment) =>
      !isPenaltyPayment(payment) &&
      String(payment.status || "").toLowerCase() === "overdue"
  ).length;

  const ownerProjectNames = scopedProjects.map((project) => project.name).filter(Boolean);

  if (!isAdminAccount(currentAccount)) {
    return (
      <>
        <PageTitle
          title="Owner Dashboard"
          subtitle={`${currentAccount?.displayName || "Project owner"} portal`}
        />

        <div className="owner-portfolio-hero" style={styles.ownerHeroCard}>
          <div>
            <span style={styles.ownerHeroEyebrow}>PROJECT OWNER PANEL</span>
            <h2 style={styles.ownerHeroTitle}>Your construction portfolio</h2>
            <p style={styles.ownerHeroText}>
              {ownerProjectNames.length
                ? ownerProjectNames.join(", ")
                : "No projects are assigned to this owner yet."}
            </p>
          </div>
          <div style={styles.ownerHeroBadge}>{scopedProjects.length} project{scopedProjects.length === 1 ? "" : "s"}</div>
        </div>

        <div className="presentation-card-grid" style={styles.cards}>
          <div className="presentation-card" style={styles.card}>
            <h3 style={styles.cardTitle}>My Projects</h3>
            <p style={styles.cardValue}>{scopedProjects.length}</p>
          </div>

          <div className="presentation-card" style={styles.card}>
            <h3 style={styles.cardTitle}>Project Members</h3>
            <p style={styles.cardValue}>{scopedUsers.length}</p>
          </div>

          <div className="presentation-card" style={styles.card}>
            <h3 style={styles.cardTitle}>Collected Amount</h3>
            <p style={styles.cardValue}>{formatValue(collectedAmount)}</p>
          </div>

          <div className="presentation-card" style={styles.card}>
            <h3 style={styles.cardTitle}>Overdue Amount</h3>
            <p style={{ ...styles.cardValue, color: overdueAmount > 0 ? "#b91c1c" : "#121a22" }}>
              {formatValue(overdueAmount)}
            </p>
          </div>

          <div className="presentation-card" style={styles.card}>
            <h3 style={styles.cardTitle}>Unpaid Amount</h3>
            <p style={styles.cardValue}>{formatValue(unpaidAmount)}</p>
          </div>
        </div>

        {success && <SuccessBox message={success} />}
        {error && <ErrorBox message={error} />}

        <div style={styles.ownerPanelGrid}>
          <div className="presentation-card" style={styles.card}>
            <h2 style={styles.sectionTitle}>Payment Health</h2>
            <div style={styles.ownerMetricRow}>
              <span>Total payment records</span>
              <strong>{scopedPayments.length}</strong>
            </div>
            <div style={styles.ownerMetricRow}>
              <span>Overdue records</span>
              <strong style={{ color: overdueCount > 0 ? "#b91c1c" : "#15803d" }}>{overdueCount}</strong>
            </div>
            <div style={styles.ownerMetricRow}>
              <span>Participants tracked</span>
              <strong>{scopedParticipants.length}</strong>
            </div>
          </div>

          <div className="presentation-card" style={styles.card}>
            <h2 style={styles.sectionTitle}>Assigned Projects</h2>
            {scopedProjects.length ? (
              <div style={styles.ownerProjectList}>
                {scopedProjects.map((project) => (
                  <div key={project.id} style={styles.ownerProjectItem}>
                    <strong>{project.name}</strong>
                    <span>{project.location || "No location"}</span>
                    <StatusBadge value={project.status} />
                  </div>
                ))}
              </div>
            ) : (
              <EmptyBox message="No projects assigned yet." />
            )}
          </div>
        </div>

        <h2 style={styles.sectionTitle}>My Projects</h2>
        <ProjectTable
          projects={scopedProjects}
          payments={scopedPayments}
          showFinancials
          canDelete
          onDeleteProject={handleDeleteProject}
          deletingProjectId={deletingProjectId}
        />
      </>
    );
  }

  return (
    <>
      <PageTitle
        title="Dashboard"
        subtitle="Admin control center for the full housing finance system"
      />

      <div className="presentation-card-grid" style={styles.cards}>
        <div className="presentation-card" style={styles.card}>
          <h3 style={styles.cardTitle}>Backend Status</h3>
          <p
            style={{
              ...styles.cardValue,
              color: backendStatus === "connected" ? "#15803d" : "#b91c1c",
            }}
          >
            {backendStatus === "checking"
              ? "Checking..."
              : backendStatus === "connected"
              ? "Connected"
              : "Disconnected"}
          </p>
        </div>

        <div className="presentation-card" style={styles.card}>
          <h3 style={styles.cardTitle}>Projects</h3>
          <p style={styles.cardValue}>{scopedProjects.length}</p>
        </div>

        <div className="presentation-card" style={styles.card}>
          <h3 style={styles.cardTitle}>Users</h3>
          <p style={styles.cardValue}>{scopedUsers.length}</p>
        </div>

        <div className="presentation-card" style={styles.card}>
          <h3 style={styles.cardTitle}>Participants</h3>
          <p style={styles.cardValue}>{scopedParticipants.length}</p>
        </div>

        <div className="presentation-card" style={styles.card}>
          <h3 style={styles.cardTitle}>Payments</h3>
          <p style={styles.cardValue}>{scopedPayments.length}</p>
        </div>
      </div>

      {success && <SuccessBox message={success} />}
      {error && <ErrorBox message={error} />}

      <h2 style={styles.sectionTitle}>Recent Projects</h2>
      <ProjectTable
        projects={scopedProjects}
        payments={scopedPayments}
        showFinancials
        canDelete
        onDeleteProject={handleDeleteProject}
        deletingProjectId={deletingProjectId}
      />
    </>
  );
}

function Projects({ currentAccount, onProjectCreatedForOwner }) {
  const [projects, setProjects] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingProjectId, setDeletingProjectId] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [form, setForm] = useState({
    name: "",
    location: "",
    neighborhood_english: "",
    total_units: "",
    average_unit_area: "",
    estimated_total_cost: "",
    start_date: "",
    expected_end_date: "",
    status: "planning",
  });

  function loadProjects() {
    setLoading(true);

    Promise.all([
      axios.get(`${API_BASE_URL}/projects/`),
      axios.get(`${API_BASE_URL}/payments/`),
    ])
      .then(([projectsResponse, paymentsResponse]) => {
        setProjects(getArrayFromResponse(projectsResponse.data));
        setPayments(getArrayFromResponse(paymentsResponse.data));
      })
      .catch((err) => {
        console.error("Projects page error:", err);
        setError(err.message || "Could not load projects.");
      })
      .finally(() => {
        setLoading(false);
      });
  }

  useEffect(() => {
    loadProjects();
  }, []);

  const scopedProjects = useMemo(() => {
    return filterProjectsByAccount(projects, currentAccount);
  }, [projects, currentAccount]);

  const scopedPayments = useMemo(() => {
    return filterPaymentsByAccount(payments, currentAccount, projects);
  }, [payments, currentAccount, projects]);

  const isAdmin = isAdminAccount(currentAccount);

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: name === "estimated_total_cost" ? formatThousands(value) : value,
    }));
  }

  function handleLocationChange(value) {
    setForm((previous) => ({
      ...previous,
      location: value,
      neighborhood_english: value === "Tehran" ? previous.neighborhood_english : "",
    }));
  }

  function handleNeighborhoodChange(value) {
    setForm((previous) => ({
      ...previous,
      neighborhood_english: value,
      location: previous.location || "Tehran",
    }));
  }

  async function handleDeleteProject(project) {
    // Owners may delete only projects visible in their scoped list; admins
    // can delete any project.  Keep this guard in addition to the UI flag.
    if (!project?.id || !canAccessProject(project, currentAccount)) return;

    const projectName = project.name || `Project ${project.id}`;
    const confirmed = window.confirm(
      `Delete "${projectName}"? This will permanently remove its payments, expenses, participants, payment plan, and prediction records.`
    );

    if (!confirmed) return;

    setError("");
    setSuccess("");
    setDeletingProjectId(project.id);

    try {
      await axios.delete(`${API_BASE_URL}/projects/${project.id}`);
      setSuccess(`Project "${projectName}" deleted successfully.`);
      loadProjects();
    } catch (err) {
      console.error("Delete project error:", err);
      setError(err.response?.data?.detail || "Could not delete project.");
    } finally {
      setDeletingProjectId(null);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!form.name.trim()) {
      setError("Project name is required.");
      return;
    }

    if (!form.location) {
      setError("Please select a city.");
      return;
    }

    if (!form.neighborhood_english) {
      setError("Please select a neighborhood.");
      return;
    }

    if (!form.total_units || Number(form.total_units) <= 0) {
      setError("Total units must be greater than zero.");
      return;
    }

    const estimatedTotalCost = cleanNumber(form.estimated_total_cost);
    if (!estimatedTotalCost || estimatedTotalCost <= 0) {
      setError("Estimated total cost must be greater than zero.");
      return;
    }

    const payload = {
      name: form.name.trim(),
      location: cleanText(form.location),
      neighborhood_english: cleanText(form.neighborhood_english),
      total_units: Number(form.total_units),
      average_unit_area: cleanNumber(form.average_unit_area),
      estimated_total_cost: estimatedTotalCost,
      start_date: form.start_date || null,
      expected_end_date: form.expected_end_date || null,
      status: form.status || "planning",
    };

    try {
      setSaving(true);

      const response = await axios.post(`${API_BASE_URL}/projects/`, payload);
      const createdProject = response.data;

      if (!isAdmin && currentAccount?.user_id && createdProject?.id) {
        await axios.post(`${API_BASE_URL}/project-owners/assign`, {
          project_id: Number(createdProject.id),
          owner_user_id: Number(currentAccount.user_id),
        });

        onProjectCreatedForOwner?.(createdProject);
      }

      setSuccess(
        isAdmin
          ? "Project created successfully."
          : "Project created and added to your owner panel."
      );

      setForm({
        name: "",
        location: "",
        neighborhood_english: "",
        total_units: "",
        average_unit_area: "",
        estimated_total_cost: "",
        start_date: "",
        expected_end_date: "",
        status: "planning",
      });

      loadProjects();
    } catch (err) {
      console.error("Create project error:", err);
      setError(
        err.response?.data?.detail ||
          "Could not create project. Check backend terminal or Swagger."
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <PageTitle
        title={isAdmin ? "Projects" : "My Projects"}
        subtitle={
          isAdmin
            ? "Create and manage pre-purchase construction projects"
            : "Create and manage projects owned by this account"
        }
      />

      <div className="presentation-card" style={styles.card}>
        <h2 style={styles.sectionTitle}>{isAdmin ? "Add New Project" : "Create New Project"}</h2>

        <form onSubmit={handleSubmit}>
          <div style={styles.formGrid}>
            <div>
              <label style={styles.label}>Project Name</label>
              <input
                name="name"
                value={form.name}
                onChange={handleChange}
                style={styles.input}
                placeholder="Example: Vanak Atlas Residence"
              />
            </div>

            <div>
              <label style={styles.label}>City</label>
              <DownwardDropdown
                value={form.location}
                onChange={handleLocationChange}
                options={CITY_OPTIONS}
                placeholder="Select city"
              />
            </div>

            <div>
              <label style={styles.label}>Neighborhood</label>
              <DownwardDropdown
                value={form.neighborhood_english}
                onChange={handleNeighborhoodChange}
                options={TEHRAN_NEIGHBORHOOD_OPTIONS}
                placeholder="Select neighborhood"
              />
            </div>

            <div>
              <label style={styles.label}>Total Units</label>
              <input
                name="total_units"
                type="number"
                value={form.total_units}
                onChange={handleChange}
                style={styles.input}
                placeholder="Example: 40"
              />
            </div>

            <div>
              <label style={styles.label}>Average Unit Area</label>
              <input
                name="average_unit_area"
                type="number"
                value={form.average_unit_area}
                onChange={handleChange}
                style={styles.input}
                placeholder="Example: 95"
              />
            </div>

            <div>
              <label style={styles.label}>Estimated Total Cost</label>
              <input
                name="estimated_total_cost"
                type="text"
                inputMode="numeric"
                value={form.estimated_total_cost}
                onChange={handleChange}
                style={styles.input}
                placeholder="Example: 850,000,000,000"
              />
            </div>

            <div>
              <label style={styles.label}>Start Date</label>
              <input
                name="start_date"
                type="date"
                value={form.start_date}
                onChange={handleChange}
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>Expected End Date</label>
              <input
                name="expected_end_date"
                type="date"
                value={form.expected_end_date}
                onChange={handleChange}
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>Status</label>
              <DownwardDropdown
                value={form.status}
                onChange={(value) => handleChange({ target: { name: "status", value } })}
                options={[
                  { value: "planning", label: "planning" },
                  { value: "active", label: "active" },
                  { value: "delayed", label: "delayed" },
                  { value: "completed", label: "completed" },
                ]}
                placeholder="Select status"
              />
            </div>
          </div>

          <button type="submit" disabled={saving} style={styles.primaryButton}>
            {saving ? "Creating..." : "Create Project"}
          </button>
        </form>
      </div>

      {success && <SuccessBox message={success} />}
      {error && <ErrorBox message={error} />}

      <h2 style={{ ...styles.sectionTitle, marginTop: "28px" }}>{isAdmin ? "Project List" : "Owned Projects"}</h2>

      {loading && <LoadingBox />}
      {!loading && (
        <ProjectTable
          projects={scopedProjects}
          payments={scopedPayments}
          showFinancials
          canDelete={Boolean(currentAccount)}
          onDeleteProject={handleDeleteProject}
          deletingProjectId={deletingProjectId}
        />
      )}
    </>
  );
}

function Users({ currentAccount }) {
  const [users, setUsers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [participants, setParticipants] = useState([]);

  const [loading, setLoading] = useState(true);
  const [savingUser, setSavingUser] = useState(false);
  const [assigning, setAssigning] = useState(false);
  const [deletingUserId, setDeletingUserId] = useState(null);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [userForm, setUserForm] = useState({
    full_name: "",
    email: "",
    phone_number: "",
    national_id: "",
    role: "buyer",
  });

  const [assignForm, setAssignForm] = useState({
    user_id: "",
    role: "buyer",
    reserved_units: "1",
    paid_amount: "0",
  });

  function loadData() {
    setLoading(true);

    Promise.all([
      axios.get(`${API_BASE_URL}/users/`),
      axios.get(`${API_BASE_URL}/projects/`),
      axios.get(`${API_BASE_URL}/participants/`),
    ])
      .then(([usersResponse, projectsResponse, participantsResponse]) => {
        const userList = getArrayFromResponse(usersResponse.data);
        const projectList = getArrayFromResponse(projectsResponse.data);
        const participantList = getArrayFromResponse(participantsResponse.data);

        setUsers(userList);
        setProjects(projectList);
        setParticipants(participantList);

        const scopedProjectList = filterProjectsByAccount(projectList, currentAccount);
        const firstProjectId = scopedProjectList[0] ? String(scopedProjectList[0].id) : "";

        setAssignForm((previous) => ({
          ...previous,
          project_id: previous.project_id || firstProjectId,
        }));
      })
      .catch((err) => {
        console.error("Users page load error:", err);
        setError("Could not load users, projects, or participants.");
      })
      .finally(() => {
        setLoading(false);
      });
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleDeleteMember(user) {
    if (!isAdminAccount(currentAccount) || !user?.id) return;
    const role = String(user.role || "").trim().toLowerCase();
    if (!["member", "buyer"].includes(role)) return;

    const confirmed = window.confirm(
      `Delete member "${user.full_name || user.email || user.id}" permanently? This removes the login account, membership requests, participant records, payments and risk records.`
    );
    if (!confirmed) return;

    setError("");
    setSuccess("");
    setDeletingUserId(user.id);
    try {
      await axios.delete(`${API_BASE_URL}/users/${user.id}`);
      setUsers((previous) => previous.filter((item) => String(item.id) !== String(user.id)));
      setParticipants((previous) => previous.filter((item) => String(item.user_id) !== String(user.id)));
      setSuccess(`Member "${user.full_name || user.email || user.id}" was deleted permanently.`);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not delete this member.");
    } finally {
      setDeletingUserId(null);
    }
  }

  const scopedProjects = useMemo(() => {
    return filterProjectsByAccount(projects, currentAccount);
  }, [projects, currentAccount]);

  const scopedParticipants = useMemo(() => {
    return filterParticipantsByAccount(participants, currentAccount, projects);
  }, [participants, currentAccount, projects]);

  const scopedUsers = useMemo(() => {
    return isAdminAccount(currentAccount)
      ? users
      : getUsersForParticipants(users, scopedParticipants);
  }, [users, scopedParticipants, currentAccount]);

  const assignedUserIds = useMemo(() => {
    return new Set(scopedParticipants.map((participant) => String(participant.user_id)));
  }, [scopedParticipants]);

  const unassignedUsers = useMemo(() => {
    return users.filter((user) => !assignedUserIds.has(String(user.id)));
  }, [users, assignedUserIds]);

  const participantRows = useMemo(() => {
    return scopedParticipants.map((participant) => {
      const project = projects.find(
        (item) => String(item.id) === String(participant.project_id)
      );

      const user = users.find(
        (item) => String(item.id) === String(participant.user_id)
      );

      return {
        id: participant.id,
        project: project ? project.name : participant.project_id,
        user: user ? user.full_name : participant.user_id,
        role: participant.role,
        reserved_units: participant.reserved_units,
        share_percent: participant.share_percent,
        paid_amount: participant.paid_amount,
        joined_at: participant.joined_at,
      };
    });
  }, [scopedParticipants, projects, users]);

  function handleUserFormChange(event) {
    const { name, value } = event.target;

    setUserForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  function handleAssignFormChange(event) {
    const { name, value } = event.target;

    setAssignForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  async function createUser(event) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!userForm.full_name.trim()) {
      setError("Full name is required.");
      return;
    }

    if (!userForm.email.trim()) {
      setError("Email is required.");
      return;
    }

    const payload = {
      full_name: userForm.full_name.trim(),
      email: userForm.email.trim(),
      phone_number: cleanText(userForm.phone_number),
      national_id: cleanText(userForm.national_id),
      role: userForm.role || "buyer",
    };

    try {
      setSavingUser(true);

      const response = await axios.post(`${API_BASE_URL}/users/`, payload);

      setSuccess(`User created successfully: ${response.data.full_name}`);

      setUserForm({
        full_name: "",
        email: "",
        phone_number: "",
        national_id: "",
        role: "buyer",
      });

      loadData();
    } catch (err) {
      console.error("Create user error:", err);
      setError(
        err.response?.data?.detail ||
          "Could not create user. Email or national ID may already exist."
      );
    } finally {
      setSavingUser(false);
    }
  }

  async function assignUserToProject(event) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!assignForm.project_id) {
      setError("Please select a project.");
      return;
    }

    if (!assignForm.user_id) {
      setError("Please select an unassigned user.");
      return;
    }

    if (!assignForm.reserved_units || Number(assignForm.reserved_units) < 1) {
      setError("Reserved units must be at least 1.");
      return;
    }

    const payload = {
      project_id: Number(assignForm.project_id),
      user_id: Number(assignForm.user_id),
      role: assignForm.role || "buyer",
      reserved_units: Number(assignForm.reserved_units),
      paid_amount: Number(assignForm.paid_amount || 0),
    };

    try {
      setAssigning(true);

      await axios.post(`${API_BASE_URL}/participants/`, payload);

      setSuccess("User assigned to project successfully.");

      setAssignForm((previous) => ({
        ...previous,
        user_id: "",
        reserved_units: "1",
        paid_amount: "0",
      }));

      loadData();
    } catch (err) {
      console.error("Assign participant error:", err);
      setError(
        err.response?.data?.detail ||
          "Could not assign user to project. The user may already be assigned or project units may be full."
      );
    } finally {
      setAssigning(false);
    }
  }

  return (
    <>
      <PageTitle
        title="Users"
        subtitle={isAdminAccount(currentAccount) ? "Create buyers and assign them to construction projects" : "View project members for this owner account"}
      />

      <div className="presentation-card-grid" style={styles.cards}>
        <div className="presentation-card" style={styles.card}>
          <h3 style={styles.cardTitle}>{isAdminAccount(currentAccount) ? "Total Users" : "Project Members"}</h3>
          <p style={styles.cardValue}>{scopedUsers.length}</p>
        </div>

        <div className="presentation-card" style={styles.card}>
          <h3 style={styles.cardTitle}>Assigned Users</h3>
          <p style={styles.cardValue}>{assignedUserIds.size}</p>
        </div>

        <div className="presentation-card" style={styles.card}>
          <h3 style={styles.cardTitle}>Unassigned Users</h3>
          <p style={styles.cardValue}>{unassignedUsers.length}</p>
        </div>
      </div>

      {isAdminAccount(currentAccount) && (
      <div className="presentation-card" style={styles.card}>
        <h2 style={styles.sectionTitle}>Add New User</h2>

        <form onSubmit={createUser}>
          <div style={styles.formGrid}>
            <div>
              <label style={styles.label}>Full Name</label>
              <input
                name="full_name"
                value={userForm.full_name}
                onChange={handleUserFormChange}
                style={styles.input}
                placeholder="Example: Ali Rezaei"
              />
            </div>

            <div>
              <label style={styles.label}>Email</label>
              <input
                name="email"
                type="email"
                value={userForm.email}
                onChange={handleUserFormChange}
                style={styles.input}
                placeholder="example@email.com"
              />
            </div>

            <div>
              <label style={styles.label}>Phone Number</label>
              <input
                name="phone_number"
                value={userForm.phone_number}
                onChange={handleUserFormChange}
                style={styles.input}
                placeholder="09121234567"
              />
            </div>

            <div>
              <label style={styles.label}>National ID</label>
              <input
                name="national_id"
                value={userForm.national_id}
                onChange={handleUserFormChange}
                style={styles.input}
                placeholder="0012345678"
              />
            </div>

            <div>
              <label style={styles.label}>Role</label>
              <DownwardDropdown
                value={userForm.role}
                onChange={(value) => handleUserFormChange({ target: { name: "role", value } })}
                options={[
                  { value: "buyer", label: "buyer" },
                  { value: "investor", label: "investor" },
                  { value: "manager", label: "manager" },
                ]}
                placeholder="Select role"
              />
            </div>
          </div>

          <button type="submit" disabled={savingUser} style={styles.primaryButton}>
            {savingUser ? "Creating..." : "Create User"}
          </button>
        </form>
      </div>
      )}

      {isAdminAccount(currentAccount) && (
      <div className="presentation-card" style={{ ...styles.card, marginTop: "22px" }}>
        <h2 style={styles.sectionTitle}>Assign User to Project</h2>

        <form onSubmit={assignUserToProject}>
          <div style={styles.formGrid}>
            <div>
              <label style={styles.label}>Project</label>
              <DownwardDropdown
                value={assignForm.project_id}
                onChange={(value) => handleAssignFormChange({ target: { name: "project_id", value } })}
                options={[
                  { value: "", label: "Select project" },
                  ...scopedProjects.map((project) => ({
                    value: String(project.id),
                    label: project.name,
                  })),
                ]}
                placeholder="Select project"
              />
            </div>

            <div>
              <label style={styles.label}>Unassigned User</label>
              <DownwardDropdown
                value={assignForm.user_id}
                onChange={(value) => handleAssignFormChange({ target: { name: "user_id", value } })}
                options={[
                  { value: "", label: "Select user" },
                  ...unassignedUsers.map((user) => ({
                    value: String(user.id),
                    label: `${user.full_name} - ${user.email}`,
                  })),
                ]}
                placeholder="Select user"
              />
            </div>

            <div>
              <label style={styles.label}>Role in Project</label>
              <DownwardDropdown
                value={assignForm.role}
                onChange={(value) => handleAssignFormChange({ target: { name: "role", value } })}
                options={[
                  { value: "buyer", label: "buyer" },
                  { value: "investor", label: "investor" },
                  { value: "partner", label: "partner" },
                ]}
                placeholder="Select role"
              />
            </div>

            <div>
              <label style={styles.label}>Reserved Units</label>
              <input
                name="reserved_units"
                type="number"
                value={assignForm.reserved_units}
                onChange={handleAssignFormChange}
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>Initial Paid Amount</label>
              <input
                name="paid_amount"
                type="number"
                value={assignForm.paid_amount}
                onChange={handleAssignFormChange}
                style={styles.input}
              />
            </div>
          </div>

          <button type="submit" disabled={assigning} style={styles.primaryButton}>
            {assigning ? "Assigning..." : "Assign to Project"}
          </button>
        </form>

        {unassignedUsers.length === 0 && (
          <p style={{ ...styles.cardText, marginTop: "14px" }}>
            All users are already assigned to a project. Create a new user first.
          </p>
        )}
      </div>
      )}

      {success && <SuccessBox message={success} />}
      {error && <ErrorBox message={error} />}

      <h2 style={{ ...styles.sectionTitle, marginTop: "28px" }}>{isAdminAccount(currentAccount) ? "User List" : "Project Member List"}</h2>

      {loading && <LoadingBox />}
      {!loading && <GenericTable
        rows={scopedUsers}
        renderActions={isAdminAccount(currentAccount) ? (user) => {
          const deletable = ["member", "buyer"].includes(String(user.role || "").toLowerCase());
          return deletable ? (
            <button
              type="button"
              style={{ ...styles.dangerButton, ...(deletingUserId === user.id ? styles.disabledButton : {}) }}
              disabled={deletingUserId === user.id}
              onClick={() => handleDeleteMember(user)}
            >
              {deletingUserId === user.id ? "Deleting..." : "Delete member"}
            </button>
          ) : <span style={{ color: "#98a2b3", fontSize: "12px" }}>Protected</span>;
        } : null}
      />}

      <h2 style={{ ...styles.sectionTitle, marginTop: "28px" }}>
        Participant Records
      </h2>

      {!loading && <GenericTable rows={participantRows} />}
    </>
  );
}

function Payments({ currentAccount }) {
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [payments, setPayments] = useState([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [projectFilter, setProjectFilter] = useState("");
  const [userFilter, setUserFilter] = useState("");
  const [scheduleProjectId, setScheduleProjectId] = useState("");

  const [form, setForm] = useState({
    user_id: "",
    amount: "",
    due_date: "",
    paid_date: "",
    payment_type: "installment",
    description: "",
  });

  const [roundForm, setRoundForm] = useState({
    due_date: "",
    installment_count: "",
    extra_cost_total: "0",
    description: "",
  });

  const [autoAmountLoading, setAutoAmountLoading] = useState(false);
  const [autoAmountSummary, setAutoAmountSummary] = useState(null);
  const [roundPreview, setRoundPreview] = useState(null);
  const [roundPlanInfo, setRoundPlanInfo] = useState(null);
  const [roundPlanLoading, setRoundPlanLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [generatingRound, setGeneratingRound] = useState(false);

  async function loadRoundPlan(projectId) {
    if (!projectId) {
      setRoundPlanInfo(null);
      setRoundForm((previous) => ({ ...previous, installment_count: "" }));
      return;
    }

    try {
      setRoundPlanLoading(true);
      const response = await axios.get(`${API_BASE_URL}/payments/project/${projectId}/plan`);
      const plan = response.data || null;
      setRoundPlanInfo(plan);
      setRoundForm((previous) => ({
        ...previous,
        installment_count: plan?.exists ? String(plan.installment_count) : "",
      }));
    } catch (err) {
      console.error("Payment plan load error:", err);
      setRoundPlanInfo(null);
      setRoundForm((previous) => ({ ...previous, installment_count: "" }));
    } finally {
      setRoundPlanLoading(false);
    }
  }

  function loadData() {
    setLoading(true);

    Promise.all([
      axios.get(`${API_BASE_URL}/projects/`),
      axios.get(`${API_BASE_URL}/users/`),
      axios.get(`${API_BASE_URL}/participants/`),
      axios.get(`${API_BASE_URL}/payments/`),
    ])
      .then(([projectsResponse, usersResponse, participantsResponse, paymentsResponse]) => {
        const projectList = getArrayFromResponse(projectsResponse.data);
        const userList = getArrayFromResponse(usersResponse.data);
        const participantList = getArrayFromResponse(participantsResponse.data);
        const paymentList = getArrayFromResponse(paymentsResponse.data);

        setProjects(projectList);
        setUsers(userList);
        setParticipants(participantList);
        setPayments(paymentList);

        const scopedProjectList = filterProjectsByAccount(projectList, currentAccount);
        const firstProjectId = scopedProjectList[0] ? String(scopedProjectList[0].id) : "";
        const scopedParticipantList = filterParticipantsByAccount(participantList, currentAccount, projectList);
        const firstParticipant = scopedParticipantList.find(
          (participant) => String(participant.project_id) === firstProjectId
        );

        setForm((previous) => ({
          ...previous,
          project_id: previous.project_id || firstProjectId,
          user_id:
            previous.user_id ||
            (firstParticipant ? String(firstParticipant.user_id) : ""),
        }));

        setRoundForm((previous) => ({
          ...previous,
          project_id: previous.project_id || firstProjectId,
        }));

        setScheduleProjectId((previous) => previous || firstProjectId);
      })
      .catch((err) => {
        console.error("Payments page load error:", err);
        setError("Could not load payments, users, projects, or participants.");
      })
      .finally(() => {
        setLoading(false);
      });
  }

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadRoundPlan(roundForm.project_id);
  }, [roundForm.project_id]);

  const scopedProjects = useMemo(() => {
    return filterProjectsByAccount(projects, currentAccount);
  }, [projects, currentAccount]);

  const scopedParticipants = useMemo(() => {
    return filterParticipantsByAccount(participants, currentAccount, projects);
  }, [participants, currentAccount, projects]);

  const scopedPayments = useMemo(() => {
    return filterPaymentsByAccount(payments, currentAccount, projects);
  }, [payments, currentAccount, projects]);

  const scopedUsers = useMemo(() => {
    return isAdminAccount(currentAccount)
      ? users
      : getUsersForParticipants(users, scopedParticipants);
  }, [users, scopedParticipants, currentAccount]);

  const memberOptions = useMemo(() => {
    return scopedParticipants
      .filter((participant) => String(participant.project_id) === String(form.project_id))
      .map((participant) => {
        const user = users.find(
          (item) => String(item.id) === String(participant.user_id)
        );

        return {
          user_id: participant.user_id,
          label: user
            ? `${user.full_name} - ${user.email}`
            : `User ${participant.user_id}`,
        };
      });
  }, [scopedParticipants, users, form.project_id]);

  useEffect(() => {
    if (!form.project_id || !form.user_id || form.payment_type !== "installment") {
      setAutoAmountSummary(null);
      return undefined;
    }

    const dueDateForCalculation =
      form.due_date || new Date().toISOString().slice(0, 10);

    let cancelled = false;

    async function calculateMemberAmount() {
      try {
        setAutoAmountLoading(true);

        const response = await axios.post(`${API_BASE_URL}/payments/next-due/member`, {
          project_id: Number(form.project_id),
          user_id: Number(form.user_id),
          due_date: dueDateForCalculation,
          extra_cost_total: 0,
          as_of_date: form.paid_date || dueDateForCalculation,
        });

        if (cancelled) return;

        const summary = response.data;
        const calculatedAmount = Math.round(Number(summary.total_due_amount || 0));

        setAutoAmountSummary(summary);
        setForm((previous) => {
          if (
            String(previous.project_id) !== String(form.project_id) ||
            String(previous.user_id) !== String(form.user_id) ||
            previous.payment_type !== "installment"
          ) {
            return previous;
          }

          return {
            ...previous,
            amount: calculatedAmount > 0 ? String(calculatedAmount) : "",
          };
        });
      } catch (err) {
        if (!cancelled) {
          console.error("Auto amount calculation error:", err);
          setAutoAmountSummary(null);
        }
      } finally {
        if (!cancelled) {
          setAutoAmountLoading(false);
        }
      }
    }

    calculateMemberAmount();

    return () => {
      cancelled = true;
    };
  }, [
    form.project_id,
    form.user_id,
    form.due_date,
    form.paid_date,
    form.payment_type,
  ]);

  function handleChange(event) {
    const { name, value } = event.target;

    if (name === "project_id") {
      const firstParticipant = scopedParticipants.find(
        (participant) => String(participant.project_id) === String(value)
      );

      setForm((previous) => ({
        ...previous,
        project_id: value,
        user_id: firstParticipant ? String(firstParticipant.user_id) : "",
        amount: "",
      }));

      return;
    }

    if (name === "payment_type" && value !== "installment") {
      setAutoAmountSummary(null);
    }

    setForm((previous) => ({
      ...previous,
      [name]: value,
      ...(name === "payment_type" && value !== "installment" ? { amount: "" } : {}),
    }));
  }

  function handleRoundChange(name, value) {
    setRoundForm((previous) => ({
      ...previous,
      [name]: value,
      ...(name === "project_id" ? { installment_count: "" } : {}),
    }));

    if (name === "project_id") {
      setRoundPlanInfo(null);
    }
    setRoundPreview(null);
  }

  function buildRoundPayload() {
    const payload = {
      project_id: Number(roundForm.project_id),
      due_date: roundForm.due_date,
      extra_cost_total: Number(roundForm.extra_cost_total || 0),
      description: cleanText(roundForm.description),
    };

    if (roundForm.installment_count) {
      payload.installment_count = Number(roundForm.installment_count);
    }
    return payload;
  }

  function validateRoundForm() {
    if (!roundForm.project_id) {
      setError("Please select a project for the payment round.");
      return false;
    }

    if (!roundForm.due_date) {
      setError("Due date is required for the payment round.");
      return false;
    }

    if (!roundPlanInfo?.exists && Number(roundForm.installment_count || 0) <= 0) {
      setError("The project owner must choose the total installment count before the first round is generated.");
      return false;
    }

    if (Number(roundForm.extra_cost_total || 0) < 0) {
      setError("Extra cost share cannot be negative.");
      return false;
    }

    return true;
  }

  async function handlePreviewRound() {
    setError("");
    setSuccess("");

    if (!validateRoundForm()) return;

    try {
      setPreviewLoading(true);
      const response = await axios.post(
        `${API_BASE_URL}/payments/next-round/preview`,
        buildRoundPayload()
      );
      setRoundPreview(response.data);
    } catch (err) {
      console.error("Preview payment round error:", err);
      setError(err.response?.data?.detail || "Could not preview the payment round.");
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handleGenerateRound() {
    setError("");
    setSuccess("");

    if (!validateRoundForm()) return;

    try {
      setGeneratingRound(true);
      const response = await axios.post(
        `${API_BASE_URL}/payments/next-round/generate`,
        buildRoundPayload()
      );

      const generatedCount = response.data?.generated_count || 0;
      const skippedCount = response.data?.skipped_count || 0;

      setSuccess(
        `Payment round generated. ${generatedCount} records created${skippedCount ? `, ${skippedCount} skipped` : ""}.`
      );
      setRoundPreview(response.data);
      setRoundPlanInfo((previous) => ({
        ...(previous || {}),
        exists: true,
        project_id: response.data?.project_id,
        project_name: response.data?.project_name,
        installment_count: response.data?.installment_count,
        created_rounds: response.data?.is_existing_round
          ? response.data?.created_rounds
          : (response.data?.created_rounds || 0) + 1,
        remaining_rounds: response.data?.rounds_remaining_after_generation,
        monthly_late_penalty_rate: response.data?.fixed_late_penalty_rate,
      }));
      setRoundForm((previous) => ({
        ...previous,
        installment_count: String(response.data?.installment_count || previous.installment_count),
      }));
      loadData();
    } catch (err) {
      console.error("Generate payment round error:", err);
      setError(err.response?.data?.detail || "Could not generate the payment round.");
    } finally {
      setGeneratingRound(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!form.project_id) {
      setError("Please select a project.");
      return;
    }

    if (!form.user_id) {
      setError("Please select a project member.");
      return;
    }

    if (!form.amount || Number(form.amount) <= 0) {
      setError("Amount must be greater than zero.");
      return;
    }

    if (!form.due_date) {
      setError("Due date is required.");
      return;
    }

    if (form.payment_type === "installment" && !form.paid_date) {
      setError("Choose the actual paid date to record an installment payment. Use Generate Payment Round to create unpaid scheduled installments.");
      return;
    }

    const payload = {
      project_id: Number(form.project_id),
      user_id: Number(form.user_id),
      amount: Number(form.amount),
      due_date: form.due_date,
      paid_date: form.paid_date || null,
      payment_type: form.payment_type || "installment",
      description: cleanText(form.description),
    };

    try {
      setSaving(true);

      if (form.payment_type === "installment") {
        const response = await axios.post(`${API_BASE_URL}/payments/installment-payment`, {
          project_id: payload.project_id,
          user_id: payload.user_id,
          amount: payload.amount,
          due_date: payload.due_date,
          paid_date: payload.paid_date,
          extra_cost_total: 0,
          description: payload.description,
        });
        setSuccess(response.data?.message || "Installment payment recorded successfully.");
      } else {
        await axios.post(`${API_BASE_URL}/payments/`, payload);
        setSuccess("Payment created successfully.");
      }

      setForm((previous) => ({
        ...previous,
        amount: "",
        due_date: "",
        paid_date: "",
        payment_type: "installment",
        description: "",
      }));

      loadData();
    } catch (err) {
      console.error("Create payment error:", err);
      setError(
        err.response?.data?.detail ||
          "Could not create payment. The selected user must be a participant in the selected project."
      );
    } finally {
      setSaving(false);
    }
  }

  const paidCount = scopedPayments.filter((payment) => payment.status === "paid").length;
  const lateCount = scopedPayments.filter((payment) => payment.status === "paid_late").length;
  const overdueCount = scopedPayments.filter((payment) => payment.status === "overdue").length;
  const unpaidCount = scopedPayments.filter((payment) => payment.status === "unpaid").length;

  const filteredPayments = scopedPayments.filter((payment) => {
    const matchesProject =
      !projectFilter || String(payment.project_id) === String(projectFilter);
  
    const matchesUser =
      !userFilter || String(payment.user_id) === String(userFilter);
  
    return matchesProject && matchesUser;
  });
  
  const scheduleProjectIdEffective =
    scheduleProjectId || projectFilter || (scopedProjects[0] ? String(scopedProjects[0].id) : "");

  const scheduleProjectPayments = useMemo(() => {
    return scopedPayments.filter(
      (payment) => String(payment.project_id) === String(scheduleProjectIdEffective)
    );
  }, [scopedPayments, scheduleProjectIdEffective]);

  const paymentSeriesSummary = useMemo(() => {
    return summarizePaymentSeries(scheduleProjectPayments);
  }, [scheduleProjectPayments]);

  const usersForProjectFilter = projectFilter
    ? scopedUsers.filter((user) =>
        scopedParticipants.some(
          (participant) =>
            String(participant.project_id) === String(projectFilter) &&
            String(participant.user_id) === String(user.id)
        )
      )
    : scopedUsers;

  return (
    <>
      <PageTitle
        title="Payments"
        subtitle={isAdminAccount(currentAccount) ? "Create payment schedules and track payment status" : "Track payment records for the owner project"}
      />

      <div className="presentation-card-grid" style={styles.cards}>
        <div className="presentation-card" style={styles.card}>
          <h3 style={styles.cardTitle}>Total Payments</h3>
          <p style={styles.cardValue}>{scopedPayments.length}</p>
        </div>

        <div className="presentation-card" style={styles.card}>
          <h3 style={styles.cardTitle}>Paid</h3>
          <p style={styles.cardValue}>{paidCount}</p>
        </div>

        <div className="presentation-card" style={styles.card}>
          <h3 style={styles.cardTitle}>Paid Late</h3>
          <p style={styles.cardValue}>{lateCount}</p>
        </div>

        <div className="presentation-card" style={styles.card}>
          <h3 style={styles.cardTitle}>Overdue</h3>
          <p style={styles.cardValue}>{overdueCount}</p>
        </div>

        <div className="presentation-card" style={styles.card}>
          <h3 style={styles.cardTitle}>Unpaid</h3>
          <p style={styles.cardValue}>{unpaidCount}</p>
        </div>
      </div>

      {!loading && (
        <PaymentScheduleAnalysis
          projects={scopedProjects}
          selectedProjectId={scheduleProjectIdEffective}
          onProjectChange={setScheduleProjectId}
          paymentSeriesSummary={paymentSeriesSummary}
          showProjectPicker={scopedProjects.length > 1}
        />
      )}

      <div className="presentation-card" style={styles.card}>
          <h2 style={styles.sectionTitle}>Generate Next Payment Round</h2>
          <p style={styles.cardText}>
            The project owner chooses the total installment count when the first round is created. After the plan starts, that count is locked so installment amounts stay consistent. Late fee is fixed at 2% of each unpaid installment for every overdue calendar month (simple, non-compounding). Existing overdue principal is shown in the preview but is never copied into the new installment record.
          </p>

          <div style={styles.formGrid}>
            <div>
              <label style={styles.label}>Project</label>
              <DownwardDropdown
                value={roundForm.project_id}
                onChange={(value) => handleRoundChange("project_id", value)}
                options={[
                  { value: "", label: "Select project" },
                  ...scopedProjects.map((project) => ({
                    value: String(project.id),
                    label: project.name,
                  })),
                ]}
                placeholder="Select project"
              />
            </div>

            <div>
              <label style={styles.label}>Due Date</label>
              <input
                type="date"
                value={roundForm.due_date}
                onChange={(event) => handleRoundChange("due_date", event.target.value)}
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>Total Installments (Owner-defined)</label>
              <input
                type="number"
                min="1"
                value={roundForm.installment_count}
                onChange={(event) => handleRoundChange("installment_count", event.target.value)}
                readOnly={Boolean(roundPlanInfo?.exists)}
                style={{
                  ...styles.input,
                  background: roundPlanInfo?.exists ? "#f7f8fc" : "#ffffff",
                }}
                placeholder={roundPlanLoading ? "Loading plan..." : "Owner chooses once"}
              />
              <p style={styles.autoAmountHint}>
                {roundPlanLoading
                  ? "Checking this project's payment plan..."
                  : roundPlanInfo?.exists
                    ? `Plan active: ${roundPlanInfo.installment_count} total installments, ${roundPlanInfo.created_rounds} round(s) created, ${roundPlanInfo.remaining_rounds} remaining.`
                    : "No payment plan yet. The owner chooses any positive installment count for this project before generating Round 1."}
              </p>
            </div>

            <div>
              <label style={styles.label}>Extra Cost Share Total</label>
              <input
                type="number"
                min="0"
                value={roundForm.extra_cost_total}
                onChange={(event) => handleRoundChange("extra_cost_total", event.target.value)}
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>Fixed Late Fee</label>
              <input value="2% / overdue month" readOnly style={{ ...styles.input, background: "#f7f8fc" }} />
            </div>

            <div>
              <label style={styles.label}>Description</label>
              <input
                value={roundForm.description}
                onChange={(event) => handleRoundChange("description", event.target.value)}
                style={styles.input}
                placeholder="Optional round note"
              />
            </div>
          </div>

          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            <button
              type="button"
              onClick={handlePreviewRound}
              disabled={previewLoading || generatingRound || roundPlanLoading}
              style={styles.secondaryButton}
            >
              {previewLoading ? "Previewing..." : "Preview Round"}
            </button>
            <button
              type="button"
              onClick={handleGenerateRound}
              disabled={generatingRound || previewLoading || roundPlanLoading}
              style={styles.primaryButton}
            >
              {generatingRound ? "Generating..." : "Generate Round"}
            </button>
          </div>

          {roundPreview && (
            <div style={{ marginTop: "18px" }}>
              <div style={styles.formGrid}>
                <div style={styles.memberRiskMetric}>
                  <span style={styles.memberRiskMetricLabel}>Round</span>
                  <strong>{roundPreview.round_number} of {roundPreview.installment_count}</strong>
                </div>
                <div style={styles.memberRiskMetric}>
                  <span style={styles.memberRiskMetricLabel}>Rounds left after this</span>
                  <strong>{roundPreview.rounds_remaining_after_generation}</strong>
                </div>
                <div style={styles.memberRiskMetric}>
                  <span style={styles.memberRiskMetricLabel}>Base installments</span>
                  <strong>{formatCompactAmount(roundPreview.total_base_installment)}</strong>
                </div>
                <div style={styles.memberRiskMetric}>
                  <span style={styles.memberRiskMetricLabel}>Previous overdue principal</span>
                  <strong>{formatCompactAmount(roundPreview.total_previous_overdue)}</strong>
                </div>
                <div style={styles.memberRiskMetric}>
                  <span style={styles.memberRiskMetricLabel}>Monthly late penalties</span>
                  <strong>{formatCompactAmount(roundPreview.total_late_penalty)}</strong>
                </div>
                <div style={styles.memberRiskMetric}>
                  <span style={styles.memberRiskMetricLabel}>Prepayment credit applied</span>
                  <strong>{formatCompactAmount(roundPreview.total_credit_amount)}</strong>
                </div>
                <div style={styles.memberRiskMetric}>
                  <span style={styles.memberRiskMetricLabel}>Total currently payable</span>
                  <strong>{formatCompactAmount(roundPreview.total_due_amount)}</strong>
                </div>
              </div>
              <p style={{ ...styles.cardText, marginTop: "12px" }}>
                {roundPreview.members?.length || 0} members in this round. Any member with unused prepayment credit will have the next base installment marked paid automatically.
              </p>
            </div>
          )}
      </div>

      <div className="presentation-card" style={styles.card}>
        <h2 style={styles.sectionTitle}>Filter Payments</h2>

        <div style={styles.formGridTwo}>
          <div>
            <label style={styles.label}>Filter by Project</label>
            <DownwardDropdown
              value={projectFilter}
              onChange={(value) => {
                setProjectFilter(value);
                setUserFilter("");
                if (value) {
                  setScheduleProjectId(value);
                }
              }}
              options={[
                { value: "", label: "All projects" },
                ...scopedProjects.map((project) => ({
                  value: String(project.id),
                  label: project.name,
                })),
              ]}
              placeholder="All projects"
            />
          </div>

          <div>
            <label style={styles.label}>Filter by User</label>
            <DownwardDropdown
              value={userFilter}
              onChange={setUserFilter}
              options={[
                { value: "", label: "All users" },
                ...usersForProjectFilter.map((user) => ({
                  value: String(user.id),
                  label: `${user.full_name} - ${user.email}`,
                })),
              ]}
              placeholder="All users"
            />
          </div>
        </div>

        <p style={{ ...styles.cardText, marginTop: "14px" }}>
          Showing {filteredPayments.length} of {scopedPayments.length} payment records.
        </p>
      </div>

      <div className="presentation-card" style={styles.card}>
        <h2 style={styles.sectionTitle}>Add Payment</h2>

        <form onSubmit={handleSubmit}>
          <div style={styles.formGrid}>
            <div>
              <label style={styles.label}>Project</label>
              <DownwardDropdown
                value={form.project_id}
                onChange={(value) => handleChange({ target: { name: "project_id", value } })}
                options={[
                  { value: "", label: "Select project" },
                  ...scopedProjects.map((project) => ({
                    value: String(project.id),
                    label: project.name,
                  })),
                ]}
                placeholder="Select project"
              />
            </div>

            <div>
              <label style={styles.label}>Project Member</label>
              <DownwardDropdown
                value={form.user_id}
                onChange={(value) => handleChange({ target: { name: "user_id", value } })}
                options={[
                  { value: "", label: "Select member" },
                  ...memberOptions.map((member) => ({
                    value: String(member.user_id),
                    label: member.label,
                  })),
                ]}
                placeholder="Select member"
              />
            </div>

            <div>
              <label style={styles.label}>Amount</label>
              <input
                name="amount"
                type="number"
                min="0"
                value={form.amount}
                onChange={handleChange}
                readOnly={form.payment_type === "installment" && !form.paid_date}
                style={{
                  ...styles.input,
                  background:
                    form.payment_type === "installment" && !form.paid_date
                      ? "#f7f8fc"
                      : "#ffffff",
                  cursor:
                    form.payment_type === "installment" && !form.paid_date
                      ? "not-allowed"
                      : "text",
                }}
                placeholder={autoAmountLoading ? "Calculating..." : "Auto-calculated"}
              />
              {form.payment_type === "installment" && (
                <p style={styles.autoAmountHint}>
                  {autoAmountLoading
                    ? "Calculating member amount..."
                    : autoAmountSummary
                      ? `Due now ${formatCompactAmount(autoAmountSummary.total_due_amount)} = base ${formatCompactAmount(autoAmountSummary.base_installment)} + old overdue ${formatCompactAmount(autoAmountSummary.previous_overdue_amount)} + monthly late fee ${formatCompactAmount(autoAmountSummary.late_penalty_amount)} + extra cost ${formatCompactAmount(autoAmountSummary.extra_cost_share_amount)} - prepayment credit ${formatCompactAmount(autoAmountSummary.credit_amount)}. To prepay, add whole multiples of ${formatCompactAmount(autoAmountSummary.base_installment)}; arbitrary amounts such as 1.2 installments are rejected.`
                      : "Select project, member, due date and paid date to calculate the exact payable amount."}
                </p>
              )}
            </div>

            <div>
              <label style={styles.label}>Due Date</label>
              <input
                name="due_date"
                type="date"
                value={form.due_date}
                onChange={handleChange}
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>Paid Date</label>
              <input
                name="paid_date"
                type="date"
                value={form.paid_date}
                onChange={handleChange}
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>Payment Type</label>
              <DownwardDropdown
                value={form.payment_type}
                onChange={(value) => handleChange({ target: { name: "payment_type", value } })}
                options={[
                  { value: "installment", label: "installment" },
                  { value: "down_payment", label: "down_payment" },
                  { value: "cost_share", label: "cost_share" },
                ]}
                placeholder="Select type"
              />
            </div>

            <div>
              <label style={styles.label}>Description</label>
              <input
                name="description"
                value={form.description}
                onChange={handleChange}
                style={styles.input}
                placeholder="Example: First installment"
              />
            </div>
          </div>

          <button type="submit" disabled={saving} style={styles.primaryButton}>
            {saving ? "Recording..." : form.payment_type === "installment" ? "Record Payment" : "Create Payment"}
          </button>
        </form>

        {memberOptions.length === 0 && (
          <p style={{ ...styles.cardText, marginTop: "14px" }}>
            This project has no participants yet. Assign a user to the project first.
          </p>
        )}
      </div>

      {success && <SuccessBox message={success} />}
      {error && <ErrorBox message={error} />}

      <h2 style={{ ...styles.sectionTitle, marginTop: "28px" }}>Payment List</h2>

      {loading && <LoadingBox />}
      {!loading && (
        <PaymentTable payments={filteredPayments} projects={scopedProjects} users={scopedUsers} />      )}
    </>
  );
}

function PredictionProgressModal({
  message,
  progress,
  currentPredictionName,
  memberCount,
}) {
  const normalizedName = String(currentPredictionName || "").toLowerCase();
  const currentStageKey = normalizedName.includes("economic")
    ? "economic"
    : normalizedName.includes("delay")
      ? "delay"
      : normalizedName.includes("member risk")
        ? "member"
        : progress >= 100
          ? "results"
          : "prepare";

  const predictionStages = [
    {
      key: "prepare",
      title: "Prepare project data",
      description: "Checking the selected project, payment schedule and participants.",
    },
    {
      key: "economic",
      title: "Economic forecast",
      description: "Forecasting the economic indicators used by this project.",
    },
    {
      key: "delay",
      title: "Project delay prediction",
      description: "Reviewing schedule, construction progress and payment signals.",
    },
    ...(memberCount > 0 ? [{
      key: "member",
      title: "Member financial risk",
      description: `${memberCount || 0} project member${memberCount === 1 ? "" : "s"} included in this run.`,
    }] : []),
    {
      key: "results",
      title: "Results ready",
      description: "Organizing the completed forecasts into the project summary.",
    },
  ];
  const currentStep = Math.max(
    0,
    predictionStages.findIndex((stage) => stage.key === currentStageKey),
  );

  return (
    <div className="prediction-progress-overlay" style={styles.modalOverlay}>
      <style>
        {`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}
      </style>

      <div className="prediction-progress-modal" style={styles.modalBoxWide}>
        <div className="prediction-modal-heading">
          <div className="prediction-orbit" aria-hidden="true">
            <span />
          </div>
          <div>
            <p className="prediction-kicker">Live prediction run</p>
            <h2 style={{ margin: "0 0 7px 0", color: "#121a22" }}>
              Running project predictions
            </h2>
            <p className="prediction-current-task">
              {currentPredictionName || "Preparing prediction services"}
            </p>
          </div>
        </div>

        <p className="prediction-live-message" style={{ margin: 0, color: "#475467", lineHeight: 1.6 }}>
          {message}
        </p>

        <div className="prediction-progress-track" style={styles.predictionProgressTrack}>
          <div
            style={{
              ...styles.predictionProgressFill,
              width: `${Math.max(0, Math.min(progress || 0, 100))}%`,
            }}
          />
        </div>

        <div className="prediction-progress-meta">
          <span>Overall progress</span>
          <strong>{Math.round(progress || 0)}%</strong>
        </div>

        <div className="prediction-stage-list" style={styles.stageList}>
          {predictionStages.map((stage, index) => {
            const state = index < currentStep
              ? "complete"
              : index === currentStep
                ? "active"
                : "waiting";

            return (
              <div
                key={stage.key}
                className={`prediction-stage-row prediction-stage-${state}`}
              >
                <span className="prediction-stage-marker">
                  {state === "complete" ? "✓" : index + 1}
                </span>
                <div className="prediction-stage-copy">
                  <div className="prediction-stage-title-row">
                    <strong>{stage.title}</strong>
                    <span>{state === "complete" ? "Completed" : state === "active" ? "Running" : "Waiting"}</span>
                  </div>
                  <p>{state === "active" ? message : stage.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function Predictions({ currentAccount }) {
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [participants, setParticipants] = useState([]);

  const [selectedProjectId, setSelectedProjectId] = useState("");

  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const streamRefs = useRef([]);

  const [predictionMessage, setPredictionMessage] = useState(
    "Preparing prediction pipeline..."
  );
  const [predictionProgress, setPredictionProgress] = useState(0);
  const [currentPredictionName, setCurrentPredictionName] = useState("");
  const [participantsPinnedOpen, setParticipantsPinnedOpen] = useState(false);
  const [participantsHoverOpen, setParticipantsHoverOpen] = useState(false);

  const [projectDelay, setProjectDelay] = useState(null);
  const [economicForecast, setEconomicForecast] = useState(null);
  const [memberRiskResults, setMemberRiskResults] = useState([]);

  function closePredictionStreams() {
    streamRefs.current.forEach((source) => {
      try {
        source.close();
      } catch {
        return;
      }
    });

    streamRefs.current = [];
  }

  useEffect(() => {
    Promise.all([
      axios.get(`${API_BASE_URL}/projects/`),
      axios.get(`${API_BASE_URL}/users/`),
      axios.get(`${API_BASE_URL}/participants/`),
    ])
      .then(([projectsResponse, usersResponse, participantsResponse]) => {
        const projectList = getArrayFromResponse(projectsResponse.data);
        const userList = getArrayFromResponse(usersResponse.data);
        const participantList = getArrayFromResponse(participantsResponse.data);

        const scopedProjectList = filterProjectsByAccount(projectList, currentAccount);

        setProjects(scopedProjectList);
        setUsers(userList);
        setParticipants(participantList);

        if (scopedProjectList.length > 0) {
          setSelectedProjectId(String(scopedProjectList[0].id));
        }
      })
      .catch((err) => {
        console.error("Predictions initial load error:", err);
        setError("Could not load projects, users, or participants.");
      })
      .finally(() => {
        setLoading(false);
      });

    return () => {
      closePredictionStreams();
    };
  }, []);

  const usersForSelectedProject = useMemo(() => {
    return users.filter((user) =>
      participants.some(
        (participant) =>
          String(participant.project_id) === String(selectedProjectId) &&
          String(participant.user_id) === String(user.id)
      )
    );
  }, [users, participants, selectedProjectId]);

  const selectedProject = useMemo(() => {
    return projects.find((project) => String(project.id) === String(selectedProjectId));
  }, [projects, selectedProjectId]);

  const participantNames = useMemo(() => {
    return usersForSelectedProject.map((user) => user.full_name || user.email || `User ${user.id}`);
  }, [usersForSelectedProject]);

  const visibleParticipantNames = participantNames.slice(0, 4);
  const hiddenParticipantNames = participantNames.slice(4);
  const hiddenParticipantCount = Math.max(0, participantNames.length - visibleParticipantNames.length);
  function handleProjectChange(event) {
    const newProjectId = event.target.value;

    closePredictionStreams();
    setRunning(false);
    setSelectedProjectId(newProjectId);
    setProjectDelay(null);
    setEconomicForecast(null);
    setMemberRiskResults([]);
    setPredictionProgress(0);
    setCurrentPredictionName("");
    setParticipantsPinnedOpen(false);
    setParticipantsHoverOpen(false);
    setError("");
  }

  function removeStreamRef(source) {
    streamRefs.current = streamRefs.current.filter((item) => item !== source);
  }

  function runStreamPrediction({
    title,
    url,
    completedStreams,
    totalStreams,
    onResult,
  }) {
    return new Promise((resolve, reject) => {
      let settled = false;
      let receivedResult = false;
      const overallBase = (completedStreams / totalStreams) * 100;
      const overallShare = 100 / totalStreams;

      setCurrentPredictionName(title);
      setPredictionMessage(`Starting ${title}...`);
      setPredictionProgress(Math.round(overallBase));

      const source = new EventSource(`${API_BASE_URL}${url}`);
      streamRefs.current.push(source);

      function finishSuccessfully(doneMessage) {
        if (settled) return;
        settled = true;

        setPredictionMessage(doneMessage || `${title} completed.`);
        setPredictionProgress(Math.round(((completedStreams + 1) / totalStreams) * 100));

        source.close();
        removeStreamRef(source);
        resolve();
      }

      function failPrediction(message) {
        if (settled) return;
        settled = true;

        source.close();
        removeStreamRef(source);
        reject(new Error(message || `${title} stream failed.`));
      }

      source.addEventListener("stage", (event) => {
        const data = JSON.parse(event.data);
        const stageProgress = Number(data.progress || 0);
        const overallProgress = overallBase + (stageProgress / 100) * overallShare;
        const stageMessage = data.message || `${title} is running...`;

        setPredictionMessage(stageMessage);
        setPredictionProgress(Math.min(99, Math.round(overallProgress)));
      });

      source.addEventListener("result", (event) => {
        const data = JSON.parse(event.data);
        receivedResult = true;
        onResult(data);
      });

      source.addEventListener("done", (event) => {
        const data = event.data ? JSON.parse(event.data) : {};

        if (!receivedResult) {
          failPrediction(`${title} finished without returning a result.`);
          return;
        }

        finishSuccessfully(data.message);
      });

      source.addEventListener("error", (event) => {
        if (settled) return;

        let message = `${title} stream failed.`;

        if ("data" in event && event.data) {
          try {
            const data = JSON.parse(event.data);
            message = data.message || message;
          } catch {
            message = `${title} stream returned an invalid error response.`;
          }
        } else if (source.readyState === EventSource.CLOSED) {
          message = `${title} stream connection was closed.`;
        }

        failPrediction(message);
      });
    });
  }

  async function runPredictions() {
    if (!selectedProjectId) {
      setError("Please select a project.");
      return;
    }

    closePredictionStreams();
    setRunning(true);
    setError("");
    setProjectDelay(null);
    setEconomicForecast(null);
    setMemberRiskResults([]);
    setPredictionProgress(0);
    setCurrentPredictionName("");
    setPredictionMessage("Opening live prediction stream...");

    const projectHorizonMonths = calculateProjectHorizonMonths(selectedProject);

    const memberRiskJobs = usersForSelectedProject.map((user) => ({
      title: `Member Risk: ${user.full_name || user.email || `User ${user.id}`}`,
      url: `/member-risk/project/${selectedProjectId}/user/${user.id}/stream`,
      onResult: (result) => {
        setMemberRiskResults((previousResults) => [
          ...previousResults.filter((item) => String(item.user_id) !== String(user.id)),
          {
            ...result,
            user_id: user.id,
            member_name: user.full_name || user.email || `User ${user.id}`,
            member_email: user.email || "",
          },
        ]);
      },
    }));

    const streamJobs = [
      {
        title: "Economic Forecast",
        url: `/ml/forecast/economic-indicators/stream?months=${projectHorizonMonths}`,
        onResult: setEconomicForecast,
      },
      {
        title: "Project Delay Prediction",
        url: `/project-delay/project/${selectedProjectId}/stream`,
        onResult: setProjectDelay,
      },
      ...memberRiskJobs,
    ];

    try {
      for (let index = 0; index < streamJobs.length; index += 1) {
        await runStreamPrediction({
          ...streamJobs[index],
          completedStreams: index,
          totalStreams: streamJobs.length,
        });
      }

      setPredictionMessage("All predictions completed.");
      setPredictionProgress(100);
    } catch (err) {
      console.error("Prediction stream error:", err);
      setError(err.message || "Prediction stream failed.");
    } finally {
      closePredictionStreams();
      setRunning(false);
      setCurrentPredictionName("");
    }
  }

  return (
    <>
      {running && (
        <PredictionProgressModal
          message={predictionMessage}
          progress={predictionProgress}
          currentPredictionName={currentPredictionName}
          memberCount={usersForSelectedProject.length}
        />
      )}

      <PageTitle
        title="Predictions"
        subtitle={isAdminAccount(currentAccount) ? "Project delay and economic forecast predictions" : "Owner-scoped project predictions"}
      />

      {loading && <LoadingBox />}
      {error && <ErrorBox message={error} />}

      {!loading && (
        <div className="prediction-workspace" style={styles.predictionControlCard}>
          <div style={styles.predictionControlHeaderCompact}>
            <div>
              <p style={styles.controlEyebrow}>Prediction workspace</p>
              <h2 style={styles.controlTitle}>Project-wide prediction run</h2>
            </div>
            <span style={styles.liveStreamPill}><span className="live-dot" style={styles.liveDot}></span>Live stages</span>
          </div>

          <div style={styles.projectPickerPanel}>
            <label style={styles.label}>Project</label>
            <DownwardDropdown
              value={selectedProjectId}
              onChange={(value) => handleProjectChange({ target: { value } })}
              options={projects.map((project) => ({
                value: String(project.id),
                label: project.name,
              }))}
              placeholder="Select project"
            />
          </div>

          <div style={styles.scopeGridCompact}>
            <div style={styles.scopeCardStrong}>
              <div style={styles.scopeIcon}>🏗</div>
              <div>
                <div style={styles.scopeTitleRow}>
                  <strong style={styles.scopeTitle}>Project Delay</strong>
                  <span style={styles.scopeBadge}>all members</span>
                </div>
                <p style={styles.scopeDescription}>
                  {selectedProject?.name || "Selected project"}
                </p>
              </div>
            </div>

            <div style={styles.scopeCard}>
              <div style={styles.scopeIcon}>👥</div>
              <div style={styles.participantContent}>
                <div style={styles.scopeTitleRow}>
                  <strong style={styles.scopeTitle}>Included participants</strong>
                  <span style={styles.scopeBadgeMuted}>{usersForSelectedProject.length} total</span>
                </div>
                <div style={styles.participantChipRow}>
                  {visibleParticipantNames.length === 0 && (
                    <span style={styles.participantMuted}>No participants</span>
                  )}

                  {visibleParticipantNames.map((name) => (
                    <span key={name} style={styles.participantChip}>{name}</span>
                  ))}

                  {hiddenParticipantCount > 0 && (
                    <span
                      style={styles.participantMoreWrap}
                      onMouseEnter={() => setParticipantsHoverOpen(true)}
                      onMouseLeave={() => setParticipantsHoverOpen(false)}
                    >
                      <button
                        type="button"
                        onClick={() => setParticipantsPinnedOpen((previous) => !previous)}
                        style={styles.participantMoreButton}
                      >
                        +{hiddenParticipantCount} more
                      </button>

                      {participantsHoverOpen && !participantsPinnedOpen && (
                        <div className="participant-hover-panel" style={styles.participantHoverPanel}>
                          {hiddenParticipantNames.map((name) => (
                            <span key={name} style={styles.participantChip}>{name}</span>
                          ))}
                        </div>
                      )}
                    </span>
                  )}
                </div>

                {hiddenParticipantCount > 0 && participantsPinnedOpen && (
                  <div className="participant-expanded-panel" style={styles.participantExpandedPanel}>
                    {hiddenParticipantNames.map((name) => (
                      <span key={name} style={styles.participantChip}>{name}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <button
            onClick={runPredictions}
            disabled={running || !selectedProjectId}
            style={{
              ...styles.primaryButton,
              ...styles.predictionRunButton,
              ...((running || !selectedProjectId) ? styles.disabledButton : {}),
            }}
          >
            {running ? "Running..." : "Run Project-wide Predictions"}
          </button>
        </div>
      )}

      {(economicForecast || projectDelay || memberRiskResults.length > 0) && (
        <div style={styles.resultGrid}>
          {economicForecast && (
            <div className="prediction-result-card" style={styles.resultBox}>
              <p style={styles.resultEyebrow}>Economic Forecast</p>
              <h2 style={styles.resultTitle}>Economic Indicators</h2>
              <div style={styles.resultMetricGrid}>
                <div className="result-metric" style={styles.resultMetric}>
                  <span>General inflation</span>
                  <strong>{formatValue(economicForecast.predicted_general_inflation_rate)}</strong>
                </div>
                <div className="result-metric" style={styles.resultMetric}>
                  <span>Housing CPI growth</span>
                  <strong>{formatValue(economicForecast.predicted_housing_cpi_growth)}</strong>
                </div>
                <div className="result-metric" style={styles.resultMetric}>
                  <span>Construction cost growth</span>
                  <strong>{formatValue(economicForecast.predicted_construction_cost_growth)}</strong>
                </div>
                <div className="result-metric" style={styles.resultMetric}>
                  <span>USD YoY growth</span>
                  <strong>{formatValue(economicForecast.predicted_usd_growth)}</strong>
                </div>
              </div>
              <p style={styles.resultNote}>
                Values are project-horizon YoY percentage estimates, not cumulative growth from today.
              </p>
              <p style={styles.resultNote}>{formatValue(economicForecast.model_note)}</p>
            </div>
          )}

          {projectDelay && (
            <div className="prediction-result-card" style={styles.resultBox}>
              <p style={styles.resultEyebrow}>Project Delay Prediction</p>
              <h2 style={styles.resultTitle}>{formatValue(projectDelay.project_name)}</h2>
              <div style={styles.resultMetricGrid}>
                <div className="result-metric" style={styles.resultMetric}>
                  <span>Delay risk level</span>
                  <strong><StatusBadge value={projectDelay.delay_risk_level} /></strong>
                </div>
                <div className="result-metric" style={styles.resultMetric}>
                  <span>Predicted delay</span>
                  <strong>{formatValue(projectDelay.predicted_delay_months)} months</strong>
                </div>
                <div className="result-metric" style={styles.resultMetric}>
                  <span>Actual duration</span>
                  <strong>{formatValue(projectDelay.estimated_actual_duration_months)} months</strong>
                </div>
                <div className="result-metric" style={styles.resultMetric}>
                  <span>Payment-based cash-flow pressure</span>
                  <strong>{formatValue(projectDelay.cash_flow_pressure_ratio)}</strong>
                </div>
              </div>
              <p style={styles.resultNote}>
                {Array.isArray(projectDelay.main_delay_factors)
                  ? projectDelay.main_delay_factors.join(", ")
                  : formatValue(projectDelay.model_note)}
              </p>
            </div>
          )}

          {memberRiskResults.length > 0 && (
            <div className="prediction-result-card" style={{ ...styles.resultBox, gridColumn: "1 / -1" }}>
              <p style={styles.resultEyebrow}>Member Risk Overview</p>
              <h2 style={styles.resultTitle}>All Project Members</h2>
              <div style={styles.memberRiskGrid}>
                {memberRiskResults.map((risk) => (
                  <div className="member-risk-card" key={risk.user_id} style={styles.memberRiskResultCard}>
                    <div style={styles.memberRiskResultHeader}>
                      <div>
                        <strong style={styles.memberRiskResultName}>{risk.member_name}</strong>
                        {risk.member_email && (
                          <p style={styles.memberRiskResultEmail}>{risk.member_email}</p>
                        )}
                      </div>
                      <StatusBadge value={risk.predicted_risk_label} />
                    </div>

                    <div style={styles.memberRiskMiniGrid}>
                      <div className="member-risk-metric" style={styles.memberRiskMetric}>
                        <span style={styles.memberRiskMetricLabel}>Risk score</span>
                        <strong style={styles.memberRiskMetricValue}>
                          {formatRiskPercent(risk.risk_score_estimate)}
                        </strong>
                      </div>

                      <div className="member-risk-metric" style={styles.memberRiskMetric}>
                        <span style={styles.memberRiskMetricLabel}>Prepaid installments</span>
                        <strong style={styles.memberRiskMetricValue}>
                          {formatValue(risk.prepaid_installment_count || 0)}
                        </strong>
                      </div>

                      <div className="member-risk-metric" style={styles.memberRiskMetric}>
                        <span style={styles.memberRiskMetricLabel}>Current payment round</span>
                        <strong style={styles.memberRiskMetricValue}>
                          {risk.recorded_rounds_total > 0
                            ? `Round ${formatValue(risk.current_round_number)} of ${formatValue(risk.recorded_rounds_total)}`
                            : "-"}
                        </strong>
                      </div>

                      <div className="member-risk-metric" style={styles.memberRiskMetric}>
                        <span style={styles.memberRiskMetricLabel}>Future rounds remaining</span>
                        <strong style={styles.memberRiskMetricValue}>
                          {formatValue(
                            Math.max(
                              Number(risk.recorded_rounds_total || 0) -
                                Number(risk.current_round_number || 0),
                              0,
                            ),
                          )}
                        </strong>
                      </div>

                      <div className="member-risk-metric" style={styles.memberRiskMetric}>
                        <span style={styles.memberRiskMetricLabel}>Remaining amount</span>
                        <strong style={styles.memberRiskMetricValue}>
                          {formatCompactAmount(risk.unpaid_amount)}
                        </strong>
                      </div>

                      <div className="member-risk-metric" style={styles.memberRiskMetric}>
                        <span style={styles.memberRiskMetricLabel}>Overdue payments</span>
                        <strong style={styles.memberRiskMetricValue}>
                          {formatValue(risk.overdue_count)}
                        </strong>
                      </div>

                      <div className="member-risk-metric" style={styles.memberRiskMetric}>
                        <span style={styles.memberRiskMetricLabel}>Late payments</span>
                        <strong style={styles.memberRiskMetricValue}>
                          {formatValue(risk.paid_late_count)}
                        </strong>
                      </div>
                    </div>

                    {(risk.risk_explanation || risk.model_note) && (
                      <p style={styles.memberRiskResultNote}>
                        {formatValue(risk.risk_explanation || risk.model_note)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [demoAccounts, setDemoAccounts] = useState(FALLBACK_DEMO_ACCOUNTS);
  const [demoAccountsLoading, setDemoAccountsLoading] = useState(true);
  const [demoAccountsError, setDemoAccountsError] = useState("");
  const [currentAccount, setCurrentAccount] = useState(null);
  const [loginError, setLoginError] = useState("");
  const [createAccountError, setCreateAccountError] = useState("");
  const [creatingAccount, setCreatingAccount] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function loadDemoAccounts() {
      setDemoAccountsLoading(true);
      setDemoAccountsError("");

      try {
        const response = await axios.get(`${API_BASE_URL}/project-owners/demo-accounts`);
        const accounts = normalizeDemoAccounts(response.data);

        if (!isMounted) return;

        setDemoAccounts(accounts);
        setCurrentAccount((previousAccount) => {
          if (previousAccount) {
            return accounts.find((account) => account.id === previousAccount.id) || null;
          }

          return getStoredDemoAccount(accounts);
        });
      } catch {
        if (!isMounted) return;

        setDemoAccounts(FALLBACK_DEMO_ACCOUNTS);
        setCurrentAccount((previousAccount) => previousAccount || getStoredDemoAccount(FALLBACK_DEMO_ACCOUNTS));
        setDemoAccountsError("Backend demo accounts could not be loaded. Showing fallback admin access.");
      } finally {
        if (isMounted) {
          setDemoAccountsLoading(false);
        }
      }
    }

    loadDemoAccounts();

    return () => {
      isMounted = false;
    };
  }, []);

  async function loginDemoAccount({ username, password }) {
    setLoginError("");
    setCreateAccountError("");

    try {
      const response = await axios.post(`${API_BASE_URL}/project-owners/login`, {
        username,
        password,
      });

      const matchedAccount = normalizeDemoAccount(response.data);

      if (!matchedAccount) {
        setLoginError("Invalid username or password.");
        return;
      }

      try {
        localStorage.setItem("housing_ai_demo_account", matchedAccount.id);
      } catch {
        // localStorage can fail in private mode; keep the in-memory demo session.
      }

      setDemoAccounts((previousAccounts) => {
        const exists = previousAccounts.some((account) => account.id === matchedAccount.id);
        return exists
          ? previousAccounts.map((account) =>
              account.id === matchedAccount.id ? matchedAccount : account
            )
          : [...previousAccounts, matchedAccount];
      });
      setCurrentAccount(matchedAccount);
    } catch (error) {
      const fallbackAccount = findDemoAccountByLogin(demoAccounts, username, password);

      if (fallbackAccount) {
        try {
          localStorage.setItem("housing_ai_demo_account", fallbackAccount.id);
        } catch {
          // localStorage can fail in private mode; keep the in-memory demo session.
        }

        setCurrentAccount(fallbackAccount);
        return;
      }

      setLoginError(error.response?.data?.detail || "Invalid username or password.");
    }
  }

  async function createOwnerAccount(accountData) {
    setLoginError("");
    setCreateAccountError("");

    if (!accountData.full_name || !accountData.email || !accountData.username || !accountData.password || !accountData.phone_number) {
      setCreateAccountError("Full name, email, username, password, and phone number are required.");
      return;
    }
    const normalizedPhone = String(accountData.phone_number).replace(/[\s-]/g, "");
    if (!/^(09\d{9}|\+989\d{9})$/.test(normalizedPhone)) {
      setCreateAccountError("Phone number must be 09123456789 or +989123456789.");
      return;
    }

    try {
      setCreatingAccount(true);
      const response = await axios.post(`${API_BASE_URL}/project-owners/create-account`, { ...accountData, phone_number: normalizedPhone });
      const createdAccount = normalizeDemoAccount(response.data);

      if (!createdAccount) {
        setCreateAccountError("Account was created, but the response could not be read.");
        return;
      }

      setDemoAccounts((previousAccounts) => {
        const exists = previousAccounts.some((account) => account.id === createdAccount.id);
        return exists
          ? previousAccounts.map((account) =>
              account.id === createdAccount.id ? createdAccount : account
            )
          : [...previousAccounts, createdAccount];
      });

      try {
        localStorage.setItem("housing_ai_demo_account", createdAccount.id);
      } catch {
        // localStorage can fail in private mode; keep the in-memory demo session.
      }

      setCurrentAccount(createdAccount);
    } catch (error) {
      setCreateAccountError(error.response?.data?.detail || "Could not create account.");
    } finally {
      setCreatingAccount(false);
    }
  }

  function switchDemoAccount() {
    try {
      localStorage.removeItem("housing_ai_demo_account");
    } catch {
      // localStorage can fail in private mode; ignore for the demo switcher.
    }

    setLoginError("");
    setCreateAccountError("");
    setCurrentAccount(null);
  }

  function handleOwnerProjectCreated(project) {
    if (!project?.id) return;

    setCurrentAccount((previousAccount) => {
      if (!previousAccount || isAdminAccount(previousAccount)) return previousAccount;

      const projectId = String(project.id);
      const projectName = project.name;
      const nextProjectIds = Array.from(new Set([...(previousAccount.projectIds || []), projectId]));
      const nextProjectNames = Array.from(new Set([...(previousAccount.projectNames || []), projectName].filter(Boolean)));

      return {
        ...previousAccount,
        projectIds: nextProjectIds,
        projectNames: nextProjectNames,
        accessLabel: nextProjectNames.join(", ") || previousAccount.accessLabel,
      };
    });
  }

  if (!currentAccount) {
    return (
      <LoginScreen
        accountsLoading={demoAccountsLoading}
        accountsError={demoAccountsError}
        loginError={loginError}
        createAccountError={createAccountError}
        creatingAccount={creatingAccount}
        onLogin={loginDemoAccount}
        onCreateAccount={createOwnerAccount}
      />
    );
  }

  return (
    <div className="presentation-app" style={styles.app}>
      <GlobalUIStyles />
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((previous) => !previous)}
        currentAccount={currentAccount}
        onSwitchAccount={switchDemoAccount}
      />

      <main className="presentation-main" style={styles.main}>
        <AppTopbar currentAccount={currentAccount} />
        <div className="presentation-page-shell">
          <AppErrorBoundary>
            <Routes>
              <Route path="/" element={<Navigate to={isMemberAccount(currentAccount) ? "/member" : "/dashboard"} replace />} />
              <Route path="/dashboard" element={isMemberAccount(currentAccount) ? <Navigate to="/member" replace /> : <Dashboard currentAccount={currentAccount} />} />
              <Route path="/projects" element={<Projects currentAccount={currentAccount} onProjectCreatedForOwner={handleOwnerProjectCreated} />} />
              <Route path="/users" element={<Users currentAccount={currentAccount} />} />
              <Route path="/payments" element={<Payments currentAccount={currentAccount} />} />
              <Route path="/predictions" element={<Predictions currentAccount={currentAccount} />} />
              <Route path="/member" element={isMemberAccount(currentAccount) ? <Member currentAccount={currentAccount} /> : <Navigate to="/dashboard" replace />} />
              <Route path="/membership-requests" element={!isAdminAccount(currentAccount) && !isMemberAccount(currentAccount) ? <MembershipRequests currentAccount={currentAccount} /> : <Navigate to={isMemberAccount(currentAccount) ? "/member" : "/dashboard"} replace />} />
            </Routes>
          </AppErrorBoundary>
        </div>
      </main>
    </div>
  );
}

const styles = {

  ownerHeroCard: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "20px",
    padding: "26px",
    borderRadius: "22px",
    background: "linear-gradient(135deg, #edf2f4 0%, #ffffff 58%, #eef1f2 100%)",
    border: "1px solid #c4d0d7",
    boxShadow: "0 18px 45px rgba(79, 113, 136, 0.10)",
    marginBottom: "22px",
  },

  ownerHeroEyebrow: {
    display: "inline-block",
    color: "#4f7188",
    fontSize: "13px",
    fontWeight: 900,
    letterSpacing: "0.12em",
    textTransform: "uppercase",
    marginBottom: "8px",
  },

  ownerHeroTitle: {
    margin: 0,
    fontSize: "28px",
    color: "#121a22",
  },

  ownerHeroText: {
    margin: "8px 0 0",
    color: "#475467",
    lineHeight: 1.6,
  },

  ownerHeroBadge: {
    padding: "12px 16px",
    borderRadius: "999px",
    background: "#4f7188",
    color: "white",
    fontWeight: 800,
    whiteSpace: "nowrap",
    boxShadow: "0 12px 24px rgba(79, 113, 136, 0.25)",
  },

  ownerPanelGrid: {
    display: "grid",
    gridTemplateColumns: "minmax(260px, 0.8fr) minmax(360px, 1.2fr)",
    gap: "18px",
    margin: "24px 0",
  },

  ownerMetricRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "14px",
    padding: "12px 0",
    borderBottom: "1px solid #eaecf0",
    color: "#475467",
  },

  ownerProjectList: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },

  ownerProjectItem: {
    display: "grid",
    gridTemplateColumns: "1.2fr 1fr auto",
    alignItems: "center",
    gap: "12px",
    padding: "12px 14px",
    border: "1px solid #eaecf0",
    borderRadius: "14px",
    background: "#f7f8fc",
    color: "#121a22",
  },

  roundSummaryGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
    gap: "12px",
  },

  roundSummaryCard: {
    padding: "14px",
    borderRadius: "14px",
    background: "#f7f8fc",
    border: "1px solid #eaecf0",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
    color: "#667085",
    fontSize: "12px",
    fontWeight: 800,
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },

  roundSummaryCardStrong: {
    padding: "14px",
    borderRadius: "14px",
    background: "#edf2f4",
    border: "1px solid #c4d0d7",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
    color: "#3b5d74",
    fontSize: "12px",
    fontWeight: 800,
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },

  mutedSmall: {
    marginTop: "4px",
    fontSize: "12px",
    color: "#667085",
    fontWeight: 500,
  },

  loginPage: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background:
      "radial-gradient(circle at top left, rgba(79, 113, 136, 0.18), transparent 34%), linear-gradient(135deg, #edf2f4 0%, #f7f8fc 52%, #eef1f2 100%)",
    fontFamily:
      "Inter, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
    padding: "32px",
    boxSizing: "border-box",
  },
  loginShell: {
    width: "min(920px, 100%)",
    display: "grid",
    gridTemplateColumns: "1.1fr 0.9fr",
    gap: "22px",
    alignItems: "stretch",
  },
  loginHeroCard: {
    borderRadius: "28px",
    padding: "34px",
    background: "#121a22",
    color: "#ffffff",
    boxShadow: "0 24px 70px rgba(18, 26, 34, 0.22)",
  },
  loginTitle: {
    margin: "10px 0 14px",
    fontSize: "42px",
    lineHeight: 1.05,
    letterSpacing: "-0.05em",
  },
  loginSubtitle: {
    color: "#cbd2df",
    lineHeight: 1.75,
    margin: 0,
    fontSize: "15px",
  },
  loginFormCard: {
    border: "1px solid #d8e1e6",
    borderRadius: "28px",
    background: "rgba(255,255,255,0.94)",
    padding: "30px",
    boxShadow: "0 24px 70px rgba(18, 26, 34, 0.12)",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  loginTabs: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "8px",
    padding: "6px",
    borderRadius: "16px",
    backgroundColor: "#f2f4f7",
    marginBottom: "18px",
  },
  loginTabButton: {
    border: "none",
    borderRadius: "12px",
    padding: "10px 12px",
    backgroundColor: "transparent",
    color: "#475467",
    fontWeight: 800,
    cursor: "pointer",
    transition: "all 0.18s ease",
  },
  loginTabButtonActive: {
    backgroundColor: "#ffffff",
    color: "#3b5d74",
    boxShadow: "0 8px 20px rgba(18, 26, 34, 0.08)",
  },
  loginCreateGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "12px",
  },
  loginFormTitle: {
    margin: "0 0 6px",
    fontSize: "28px",
    letterSpacing: "-0.04em",
    color: "#121a22",
  },
  loginErrorCard: {
    padding: "12px 14px",
    borderRadius: "14px",
    background: "#fef2f2",
    border: "1px solid #fecaca",
    color: "#991b1b",
    fontWeight: 800,
    fontSize: "13px",
  },
  loginCards: {
    display: "grid",
    gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
    gap: "18px",
  },
  loginStatusCard: {
    padding: "14px 16px",
    borderRadius: "16px",
    background: "rgba(79, 113, 136, 0.08)",
    border: "1px solid rgba(79, 113, 136, 0.18)",
    color: "#334f61",
    fontWeight: 700,
  },
  loginWarningCard: {
    padding: "14px 16px",
    borderRadius: "16px",
    background: "rgba(245, 158, 11, 0.1)",
    border: "1px solid rgba(245, 158, 11, 0.25)",
    color: "#92400e",
    fontWeight: 700,
  },
  loginAccountCard: {
    textAlign: "left",
    border: "1px solid #d8e1e6",
    borderRadius: "24px",
    background: "rgba(255,255,255,0.92)",
    padding: "24px",
    cursor: "pointer",
    boxShadow: "0 18px 45px rgba(18, 26, 34, 0.10)",
    transition: "transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease",
    display: "flex",
    flexDirection: "column",
    minHeight: "260px",
  },
  loginRolePill: {
    width: "fit-content",
    borderRadius: "999px",
    padding: "6px 10px",
    background: "#edf2f4",
    color: "#4f7188",
    fontWeight: 800,
    fontSize: "12px",
    marginBottom: "18px",
  },
  loginAccountName: {
    fontSize: "23px",
    color: "#121a22",
    marginBottom: "6px",
  },
  loginAccountEmail: {
    color: "#667085",
    fontSize: "13px",
  },
  loginAccountText: {
    color: "#475467",
    lineHeight: 1.65,
    margin: "18px 0 0",
  },
  loginOpenText: {
    marginTop: "auto",
    color: "#4f7188",
    fontWeight: 800,
  },
  sidebarAccountCard: {
    marginTop: "22px",
    borderRadius: "18px",
    background: "rgba(255,255,255,0.08)",
    border: "1px solid rgba(255,255,255,0.12)",
    padding: "14px",
  },
  sidebarAccountRole: {
    display: "inline-flex",
    color: "#b8c8d2",
    fontSize: "11px",
    fontWeight: 900,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    marginBottom: "8px",
  },
  sidebarAccountName: {
    display: "block",
    color: "#ffffff",
    fontSize: "14px",
  },
  sidebarAccountText: {
    color: "#cbd2df",
    fontSize: "12px",
    lineHeight: 1.45,
    margin: "6px 0 12px",
  },
  sidebarAccountButton: {
    width: "100%",
    border: "1px solid rgba(255,255,255,0.16)",
    borderRadius: "12px",
    background: "rgba(255,255,255,0.10)",
    color: "#ffffff",
    padding: "9px 10px",
    cursor: "pointer",
    fontWeight: 800,
  },
  sidebarCollapsedAccount: {
    marginTop: "20px",
    width: "44px",
    height: "44px",
    borderRadius: "14px",
    border: "1px solid rgba(255,255,255,0.14)",
    background: "rgba(79, 113, 136,0.28)",
    color: "#ffffff",
    fontWeight: 900,
    cursor: "pointer",
    alignSelf: "center",
  },
  app: {
    minHeight: "100vh",
    display: "flex",
    backgroundColor: "#f7f8fc",
    color: "#121a22",
    fontFamily:
      "Inter, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
  },
  sidebar: {
    width: "250px",
    minHeight: "100vh",
    backgroundColor: "#121a22",
    color: "#ffffff",
    padding: "24px 18px",
    boxSizing: "border-box",
    transition: "width 0.25s ease, padding 0.25s ease",
  },
  logo: {
    fontSize: "22px",
    margin: 0,
    whiteSpace: "nowrap",
  },

  sidebarCollapsed: {
    width: "88px",
    padding: "24px 14px",
  },
  
  sidebarHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "10px",
    marginBottom: "32px",
  },
  
  logoCollapsed: {
    fontSize: "20px",
  },
  
  sidebarToggle: {
    width: "34px",
    height: "34px",
    border: "1px solid rgba(255,255,255,0.16)",
    borderRadius: "10px",
    backgroundColor: "rgba(255,255,255,0.08)",
    color: "#ffffff",
    cursor: "pointer",
    fontSize: "18px",
    lineHeight: 1,
  },
  
  navLinkCollapsed: {
    justifyContent: "center",
    padding: "12px 8px",
  },
  
  navIcon: {
    width: "28px",
    height: "28px",
    borderRadius: "8px",
    backgroundColor: "rgba(255,255,255,0.08)",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "12px",
    fontWeight: 800,
    flexShrink: 0,
  },

  nav: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  navLink: {
    color: "#cbd2df",
    textDecoration: "none",
    padding: "12px 14px",
    borderRadius: "10px",
    fontSize: "15px",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    minHeight: "44px",
    boxSizing: "border-box",
  },
  navLinkActive: {
    backgroundColor: "#4f7188",
    color: "#ffffff",
  },
  main: {
    flex: 1,
    padding: "36px 34px",
    boxSizing: "border-box",
    overflowX: "auto",
    background: "radial-gradient(circle at top left, rgba(79, 113, 136, 0.06), transparent 28%), #f7f8fc",
  },
  pageTitle: {
    marginBottom: "24px",
  },
  h1: {
    margin: "0 0 8px 0",
    fontSize: "32px",
    letterSpacing: "-0.03em",
  },
  subtitle: {
    margin: 0,
    color: "#667085",
    fontSize: "15px",
  },
  cards: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "18px",
    marginBottom: "28px",
  },
  card: {
    backgroundColor: "rgba(255, 255, 255, 0.92)",
    borderRadius: "18px",
    padding: "22px",
    boxShadow: "0 10px 30px rgba(18, 26, 34, 0.06)",
    border: "1px solid #e4e7ec",
    marginBottom: "18px",
    transition: "transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease",
    backdropFilter: "blur(8px)",
  },
  cardTitle: {
    margin: "0 0 12px 0",
    color: "#475467",
    fontSize: "15px",
    fontWeight: 600,
  },
  cardValue: {
    margin: 0,
    fontSize: "24px",
    fontWeight: 700,
  },
  cardText: {
    margin: 0,
    color: "#667085",
    lineHeight: 1.6,
  },
  sectionTitle: {
    fontSize: "20px",
    margin: "0 0 14px 0",
  },
  tableWrapper: {
    backgroundColor: "#ffffff",
    borderRadius: "18px",
    overflow: "auto",
    border: "1px solid #e4e7ec",
    boxShadow: "0 10px 30px rgba(18, 26, 34, 0.06)",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    minWidth: "900px",
  },
  th: {
    textAlign: "left",
    padding: "14px 16px",
    backgroundColor: "#f2f4f7",
    borderBottom: "1px solid #e4e7ec",
    fontSize: "14px",
    color: "#344054",
  },
  td: {
    padding: "14px 16px",
    borderBottom: "1px solid #e4e7ec",
    fontSize: "14px",
    color: "#121a22",
    verticalAlign: "top",
  },
  projectProgressCell: {
    minWidth: "110px",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    color: "#667085",
    fontSize: "12px",
    fontWeight: 700,
  },
  projectProgressTrack: {
    width: "70px",
    height: "7px",
    borderRadius: "999px",
    backgroundColor: "#e4e7ec",
    overflow: "hidden",
  },
  projectProgressFill: {
    height: "100%",
    borderRadius: "999px",
    backgroundColor: "#4f7188",
    transition: "width 0.25s ease",
  },
  infoBox: {
    backgroundColor: "#ffffff",
    border: "1px solid #e4e7ec",
    borderRadius: "12px",
    padding: "16px",
    color: "#475467",
    marginBottom: "18px",
  },
  successBox: {
    backgroundColor: "#f0fdf4",
    border: "1px solid #bbf7d0",
    borderRadius: "12px",
    padding: "16px",
    color: "#166534",
    marginBottom: "18px",
  },
  errorBox: {
    backgroundColor: "#fef2f2",
    border: "1px solid #fecaca",
    borderRadius: "12px",
    padding: "16px",
    color: "#991b1b",
    marginBottom: "18px",
  },
  formGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  input: {
    width: "100%",
    padding: "11px 13px",
    borderRadius: "12px",
    border: "1px solid #cbd2df",
    fontSize: "14px",
    boxSizing: "border-box",
    backgroundColor: "#ffffff",
  },
  readOnlyInput: {
    width: "100%",
    padding: "13px 16px",
    borderRadius: "14px",
    border: "1px solid #e2e8eb",
    background: "#f7f8fc",
    color: "#121a22",
    fontWeight: 800,
    minHeight: "46px",
    display: "flex",
    alignItems: "center",
  },

  autoAmountHint: {
    margin: "8px 0 0",
    color: "#667085",
    fontSize: "13px",
    lineHeight: 1.45,
  },

  label: {
    display: "block",
    marginBottom: "6px",
    fontSize: "14px",
    fontWeight: 600,
    color: "#344054",
  },
  dropdownShell: {
    position: "relative",
    width: "100%",
    zIndex: 1,
  },
  dropdownShellOpen: {
    zIndex: 5000,
  },
  dropdownButton: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    textAlign: "left",
    cursor: "pointer",
  },
  dropdownButtonOpen: {
    borderColor: "#4f7188",
    boxShadow: "0 0 0 4px rgba(79, 113, 136, 0.12)",
  },
  dropdownButtonText: {
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    paddingRight: "10px",
  },
  dropdownChevron: {
    color: "#667085",
    transition: "transform 0.18s ease",
    fontSize: "16px",
    lineHeight: 1,
  },
  dropdownPanel: {
    position: "absolute",
    top: "calc(100% + 8px)",
    left: 0,
    right: 0,
    maxHeight: "260px",
    overflowY: "auto",
    borderRadius: "14px",
    border: "1px solid #cbd2df",
    backgroundColor: "#ffffff",
    boxShadow: "0 18px 45px rgba(18, 26, 34, 0.16)",
    padding: "6px",
    zIndex: 6000,
  },
  dropdownOption: {
    width: "100%",
    display: "block",
    textAlign: "left",
    padding: "10px 11px",
    border: "none",
    borderRadius: "10px",
    backgroundColor: "transparent",
    color: "#121a22",
    cursor: "pointer",
    fontSize: "14px",
    boxShadow: "none",
  },
  dropdownOptionActive: {
    backgroundColor: "#edf2f4",
    color: "#3b5d74",
    fontWeight: 800,
  },

  dropdownSearchWrap: {
    position: "sticky",
    top: 0,
    zIndex: 1,
    padding: "4px",
    marginBottom: "4px",
    backgroundColor: "#ffffff",
  },
  dropdownSearchInput: {
    width: "100%",
    boxSizing: "border-box",
    padding: "10px 11px",
    borderRadius: "10px",
    border: "1px solid #cbd2df",
    outline: "none",
    fontSize: "14px",
    color: "#121a22",
    backgroundColor: "#f7f8fc",
  },
  dropdownOptionMeta: {
    display: "block",
    marginTop: "3px",
    color: "#667085",
    fontSize: "12px",
    fontWeight: 600,
  },
  dropdownEmpty: {
    padding: "12px",
    color: "#667085",
    fontSize: "13px",
    textAlign: "center",
  },

  formGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "16px",
  },
  formGridTwo: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
    gap: "16px",
  },
  primaryButton: {
    marginTop: "16px",
    padding: "12px 18px",
    borderRadius: "12px",
    border: "none",
    background: "linear-gradient(135deg, #4f7188, #3b5d74)",
    color: "#ffffff",
    fontWeight: 700,
    cursor: "pointer",
    boxShadow: "0 10px 22px rgba(79, 113, 136, 0.18)",
  },
  secondaryButton: {
    marginTop: "12px",
    padding: "9px 12px",
    borderRadius: "10px",
    border: "1px solid #cbd2df",
    backgroundColor: "#ffffff",
    color: "#344054",
    fontWeight: 700,
    cursor: "pointer",
  },
  dangerButton: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "6px",
    padding: "8px 11px",
    borderRadius: "10px",
    border: "1px solid #fecaca",
    backgroundColor: "#fff1f2",
    color: "#b42318",
    fontWeight: 700,
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  disabledButton: {
    opacity: 0.6,
    cursor: "not-allowed",
  },
  paymentSeriesPanel: {
    backgroundColor: "#ffffff",
    border: "1px dashed #c4d0d7",
    borderRadius: "16px",
    padding: "16px",
    marginBottom: "16px",
    boxShadow: "0 10px 24px rgba(79, 113, 136, 0.05)",
  },
  paymentSeriesHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: "12px",
    marginBottom: "12px",
  },
  paymentSeriesTitle: {
    margin: 0,
    color: "#121a22",
    fontSize: "18px",
  },
  paymentSeriesTable: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    marginTop: "12px",
    maxHeight: "220px",
    overflowY: "auto",
  },
  paymentSeriesRow: {
    display: "grid",
    gridTemplateColumns: "90px repeat(5, minmax(110px, 1fr))",
    gap: "8px",
    alignItems: "center",
    padding: "10px 12px",
    borderRadius: "12px",
    backgroundColor: "#f7f8fc",
    border: "1px solid #e4e7ec",
    color: "#344054",
    fontSize: "12px",
  },

  predictionControlCard: {
    background: "linear-gradient(135deg, rgba(79, 113, 136, 0.08), rgba(95, 121, 139, 0.04)), #ffffff",
    borderRadius: "22px",
    padding: "24px",
    boxShadow: "0 18px 45px rgba(18, 26, 34, 0.08)",
    border: "1px solid #d8e1e6",
    marginBottom: "22px",
  },
  predictionControlHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: "18px",
    marginBottom: "18px",
  },
  controlEyebrow: {
    margin: "0 0 6px 0",
    fontSize: "12px",
    letterSpacing: "0.1em",
    textTransform: "uppercase",
    color: "#4f7188",
    fontWeight: 800,
  },
  controlTitle: {
    margin: "0 0 8px 0",
    fontSize: "23px",
    color: "#121a22",
  },
  controlSubtitle: {
    margin: 0,
    color: "#475467",
    lineHeight: 1.65,
    maxWidth: "780px",
  },
  liveStreamPill: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "7px 11px",
    borderRadius: "999px",
    backgroundColor: "#edf2f4",
    color: "#3b5d74",
    fontSize: "12px",
    fontWeight: 800,
    whiteSpace: "nowrap",
    border: "1px solid #c4d0d7",
  },
  projectPickerPanel: {
    backgroundColor: "#ffffff",
    border: "1px solid #c4d0d7",
    borderRadius: "16px",
    padding: "16px",
    marginBottom: "16px",
    boxShadow: "0 10px 24px rgba(79, 113, 136, 0.06)",
  },
  scopeGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
    gap: "12px",
    marginBottom: "16px",
  },
  scopeCard: {
    display: "flex",
    alignItems: "flex-start",
    gap: "12px",
    backgroundColor: "rgba(255, 255, 255, 0.86)",
    border: "1px solid #e4e7ec",
    borderRadius: "16px",
    padding: "14px",
  },
  scopeCardStrong: {
    display: "flex",
    alignItems: "flex-start",
    gap: "12px",
    backgroundColor: "#edf2f4",
    border: "1px solid #c4d0d7",
    borderRadius: "16px",
    padding: "14px",
  },
  scopeIcon: {
    width: "38px",
    height: "38px",
    borderRadius: "13px",
    backgroundColor: "#ffffff",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    fontSize: "18px",
  },
  scopeTitleRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    flexWrap: "wrap",
    marginBottom: "4px",
  },
  scopeTitle: {
    color: "#121a22",
    fontSize: "14px",
  },
  scopeBadge: {
    padding: "3px 7px",
    borderRadius: "999px",
    backgroundColor: "#d8e1e6",
    color: "#3b5d74",
    fontSize: "11px",
    fontWeight: 800,
  },
  scopeBadgeMuted: {
    padding: "3px 7px",
    borderRadius: "999px",
    backgroundColor: "#f2f4f7",
    color: "#475467",
    fontSize: "11px",
    fontWeight: 800,
  },
  scopeDescription: {
    margin: 0,
    color: "#667085",
    fontSize: "13px",
    lineHeight: 1.5,
  },
  memberRiskPanel: {
    display: "grid",
    gridTemplateColumns: "minmax(0, 1fr) minmax(240px, 320px)",
    gap: "16px",
    alignItems: "stretch",
    backgroundColor: "#f7f8fc",
    border: "1px dashed #cbd2df",
    borderRadius: "18px",
    padding: "16px",
    marginBottom: "14px",
  },
  memberRiskText: {
    minWidth: 0,
  },
  memberRiskTitle: {
    margin: "0 0 8px 0",
    color: "#121a22",
    fontSize: "18px",
  },
  memberRiskDescription: {
    margin: 0,
    color: "#667085",
    lineHeight: 1.6,
  },
  selectedMemberBox: {
    backgroundColor: "#ffffff",
    border: "1px solid #e4e7ec",
    borderRadius: "14px",
    padding: "14px",
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-start",
  },
  selectedMemberLabel: {
    fontSize: "12px",
    fontWeight: 800,
    color: "#667085",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    marginBottom: "6px",
  },
  selectedMemberName: {
    color: "#121a22",
    fontSize: "15px",
    lineHeight: 1.35,
  },
  selectedMemberEmail: {
    color: "#667085",
    fontSize: "13px",
    marginTop: "4px",
    wordBreak: "break-word",
  },
  memberCardGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
    gap: "10px",
    marginBottom: "16px",
  },
  memberOptionCard: {
    width: "100%",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    textAlign: "left",
    border: "1px solid #e4e7ec",
    backgroundColor: "#ffffff",
    borderRadius: "14px",
    padding: "12px",
    cursor: "pointer",
  },
  memberOptionCardActive: {
    border: "1px solid #4f7188",
    boxShadow: "0 0 0 3px rgba(79, 113, 136, 0.12)",
    backgroundColor: "#edf2f4",
  },
  memberAvatar: {
    width: "34px",
    height: "34px",
    borderRadius: "12px",
    backgroundColor: "#d8e1e6",
    color: "#3b5d74",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: 900,
    flexShrink: 0,
  },
  memberOptionText: {
    display: "flex",
    flexDirection: "column",
    minWidth: 0,
    flex: 1,
  },
  memberSelectedPill: {
    padding: "4px 7px",
    borderRadius: "999px",
    backgroundColor: "#4f7188",
    color: "#ffffff",
    fontSize: "11px",
    fontWeight: 800,
  },
  memberOptionEmpty: {
    padding: "14px",
    borderRadius: "14px",
    backgroundColor: "#ffffff",
    border: "1px solid #e4e7ec",
    color: "#667085",
  },
  predictionActionRow: {
    display: "flex",
    alignItems: "center",
    gap: "14px",
    flexWrap: "wrap",
  },
  predictionRunButton: {
    marginTop: 0,
    minWidth: "230px",
    boxShadow: "0 12px 24px rgba(79, 113, 136, 0.22)",
  },
  actionHint: {
    margin: 0,
    color: "#667085",
    fontSize: "13px",
    lineHeight: 1.45,
  },
  predictionControlHeaderCompact: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "18px",
    marginBottom: "18px",
  },
  liveDot: {
    width: "8px",
    height: "8px",
    borderRadius: "999px",
    backgroundColor: "#4f7188",
    display: "inline-block",
    marginRight: "7px",
  },
  scopeGridCompact: {
    display: "grid",
    gridTemplateColumns: "minmax(260px, 0.8fr) minmax(320px, 1.2fr)",
    gap: "12px",
    marginBottom: "16px",
  },
  participantChipRow: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    flexWrap: "wrap",
    position: "relative",
  },
  participantContent: {
    flex: 1,
    minWidth: 0,
  },
  participantChip: {
    padding: "5px 8px",
    borderRadius: "999px",
    backgroundColor: "#f2f4f7",
    color: "#344054",
    fontSize: "12px",
    fontWeight: 700,
  },
  participantMoreWrap: {
    position: "relative",
    display: "inline-flex",
    zIndex: 40,
  },
  participantMoreButton: {
    padding: "5px 8px",
    borderRadius: "999px",
    backgroundColor: "#d8e1e6",
    color: "#3b5d74",
    fontSize: "12px",
    fontWeight: 800,
    border: "none",
    cursor: "pointer",
    boxShadow: "none",
    margin: 0,
  },
  participantExpandedPanel: {
    display: "flex",
    flexWrap: "wrap",
    gap: "6px",
    marginTop: "10px",
    paddingTop: "10px",
    borderTop: "1px solid #e4e7ec",
  },
  participantHoverPanel: {
    position: "absolute",
    top: "calc(100% + 8px)",
    right: 0,
    minWidth: "220px",
    maxWidth: "320px",
    display: "flex",
    flexWrap: "wrap",
    gap: "6px",
    padding: "10px",
    borderRadius: "14px",
    border: "1px solid #cbd2df",
    backgroundColor: "#ffffff",
    boxShadow: "0 18px 45px rgba(18, 26, 34, 0.16)",
    zIndex: 3000,
  },
  participantMuted: {
    color: "#667085",
    fontSize: "13px",
  },
  resultGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
    gap: "18px",
  },
  resultEyebrow: {
    margin: "0 0 6px 0",
    color: "#4f7188",
    fontSize: "12px",
    fontWeight: 900,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
  },
  resultTitle: {
    margin: "0 0 14px 0",
    color: "#121a22",
    fontSize: "20px",
  },
  resultMetricGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
    gap: "10px",
  },
  resultMetric: {
    backgroundColor: "#f7f8fc",
    border: "1px solid #e4e7ec",
    borderRadius: "14px",
    padding: "12px",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
    color: "#667085",
    fontSize: "12px",
  },
  memberRiskGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
    gap: "14px",
  },
  memberRiskResultCard: {
    backgroundColor: "#f7f8fc",
    border: "1px solid #e4e7ec",
    borderRadius: "18px",
    padding: "16px",
    overflow: "hidden",
  },
  memberRiskResultHeader: {
    display: "flex",
    justifyContent: "space-between",
    gap: "12px",
    alignItems: "flex-start",
    marginBottom: "14px",
  },
  memberRiskResultName: {
    color: "#121a22",
    fontSize: "15px",
  },
  memberRiskResultEmail: {
    margin: "4px 0 0 0",
    color: "#667085",
    fontSize: "12px",
    wordBreak: "break-word",
  },
  memberRiskMiniGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
    gap: "10px",
  },
  memberRiskMetric: {
    minWidth: 0,
    backgroundColor: "#ffffff",
    border: "1px solid #e4e7ec",
    borderRadius: "14px",
    padding: "10px",
    display: "flex",
    flexDirection: "column",
    gap: "5px",
  },
  memberRiskMetricLabel: {
    color: "#667085",
    fontSize: "11px",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  memberRiskMetricValue: {
    color: "#121a22",
    fontSize: "17px",
    fontWeight: 800,
    lineHeight: 1.1,
    whiteSpace: "nowrap",
  },
  memberForecastScope: {
    marginTop: "12px",
    padding: "12px",
    borderRadius: "14px",
    border: "1px solid #c4d0d7",
    backgroundColor: "#edf2f4",
  },
  memberForecastScopeHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "10px",
    marginBottom: "10px",
  },
  memberForecastScopeTitle: {
    color: "#263e4e",
    fontSize: "13px",
  },
  memberForecastScopeBadge: {
    padding: "4px 8px",
    borderRadius: "999px",
    backgroundColor: "#d8e1e6",
    color: "#3b5d74",
    fontSize: "11px",
    fontWeight: 800,
  },
  memberForecastScopeGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
    gap: "8px",
  },
  memberForecastScopeItem: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "8px",
    padding: "7px 8px",
    borderRadius: "10px",
    backgroundColor: "rgba(255,255,255,0.78)",
    color: "#667085",
    fontSize: "11px",
  },
  memberForecastScopeNote: {
    margin: "10px 0 0",
    color: "#475467",
    fontSize: "11px",
    lineHeight: 1.55,
  },
  memberRiskResultNote: {
    margin: "12px 0 0 0",
    color: "#667085",
    lineHeight: 1.5,
    fontSize: "12px",
  },
  resultNote: {
    margin: "14px 0 0 0",
    color: "#667085",
    lineHeight: 1.55,
    fontSize: "13px",
  },
  resultBox: {
    backgroundColor: "#ffffff",
    border: "1px solid #e4e7ec",
    borderRadius: "18px",
    padding: "20px",
    marginBottom: "18px",
    boxShadow: "0 10px 30px rgba(18, 26, 34, 0.06)",
  },
  badge: {
    display: "inline-block",
    padding: "5px 9px",
    borderRadius: "999px",
    fontSize: "12px",
    fontWeight: 700,
  },
  badgeDefault: {
    backgroundColor: "#e4e7ec",
    color: "#344054",
  },
  badgeGreen: {
    backgroundColor: "#dcfce7",
    color: "#166534",
  },
  badgeYellow: {
    backgroundColor: "#fef9c3",
    color: "#854d0e",
  },
  badgeRed: {
    backgroundColor: "#fee2e2",
    color: "#991b1b",
  },
  badgePurple: {
    backgroundColor: "#f5e9ef",
    color: "#6c3f54",
  },
  modalOverlay: {
    position: "fixed",
    inset: 0,
    backgroundColor: "rgba(18, 26, 34, 0.55)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 9999,
    animation: "smoothOverlayIn 0.18s ease both",
  },
  modalBox: {
    width: "420px",
    backgroundColor: "#ffffff",
    borderRadius: "20px",
    padding: "28px",
    boxShadow: "0 25px 50px rgba(18, 26, 34, 0.25)",
    textAlign: "center",
    animation: "smoothModalIn 0.2s ease both",
  },
  spinner: {
    width: "54px",
    height: "54px",
    border: "6px solid #d8e1e6",
    borderTop: "6px solid #4f7188",
    borderRadius: "50%",
    margin: "0 auto 20px auto",
    animation: "spin 0.9s linear infinite",
  },
  modalBoxWide: {
    width: "520px",
    maxWidth: "calc(100vw - 32px)",
    maxHeight: "calc(100vh - 48px)",
    overflowY: "auto",
    backgroundColor: "#ffffff",
    borderRadius: "20px",
    padding: "28px",
    boxShadow: "0 25px 50px rgba(18, 26, 34, 0.25)",
    textAlign: "center",
    animation: "smoothModalIn 0.2s ease both",
  },
  modalEyebrow: {
    margin: "0 0 10px 0",
    fontSize: "13px",
    fontWeight: 700,
    color: "#4f7188",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
  },
  predictionProgressTrack: {
    width: "100%",
    height: "9px",
    borderRadius: "999px",
    backgroundColor: "#e4e7ec",
    overflow: "hidden",
    marginTop: "18px",
  },
  predictionProgressFill: {
    height: "100%",
    borderRadius: "999px",
    backgroundColor: "#4f7188",
    transition: "width 0.25s ease",
  },
  progressText: {
    margin: "8px 0 16px 0",
    fontSize: "13px",
    color: "#667085",
  },
  stageList: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    textAlign: "left",
  },
  stageRow: {
    display: "flex",
    alignItems: "flex-start",
    gap: "10px",
    padding: "10px 12px",
    borderRadius: "12px",
    backgroundColor: "#f7f8fc",
    border: "1px solid #e4e7ec",
  },
  stageCheck: {
    width: "22px",
    height: "22px",
    borderRadius: "999px",
    backgroundColor: "#dcfce7",
    color: "#166534",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "13px",
    fontWeight: 800,
    flexShrink: 0,
  },
  stageTitle: {
    display: "block",
    fontSize: "12px",
    color: "#344054",
    marginBottom: "3px",
  },
  stageMessage: {
    margin: 0,
    fontSize: "13px",
    color: "#667085",
    lineHeight: 1.4,
  },
  boundaryBox: {
    padding: "40px",
    fontFamily: "Arial",
  },
  boundaryPre: {
    backgroundColor: "#fef2f2",
    border: "1px solid #fecaca",
    padding: "16px",
    borderRadius: "12px",
    color: "#991b1b",
    whiteSpace: "pre-wrap",
  },
};

export default App;
