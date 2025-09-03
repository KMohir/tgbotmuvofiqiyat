--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: admins; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.admins (
    user_id bigint NOT NULL
);


ALTER TABLE public.admins OWNER TO postgres;

--
-- Name: group_video_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.group_video_settings (
    chat_id text NOT NULL,
    centris_enabled integer DEFAULT 0,
    centris_start_video integer DEFAULT 0,
    golden_enabled integer DEFAULT 0,
    golden_start_video integer DEFAULT 0,
    viewed_videos text DEFAULT '[]'::text,
    is_subscribed integer DEFAULT 1,
    centris_season_id integer,
    golden_season_id integer,
    group_name text DEFAULT 'Noma''lum guruh'::text,
    centris_viewed_videos text DEFAULT '[]'::text,
    golden_viewed_videos text DEFAULT '[]'::text,
    send_times text DEFAULT '["08:00", "20:00"]'::text
);


ALTER TABLE public.group_video_settings OWNER TO postgres;

--
-- Name: group_whitelist; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.group_whitelist (
    id integer NOT NULL,
    chat_id bigint,
    title text,
    status text DEFAULT 'active'::text,
    added_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    added_by bigint
);


ALTER TABLE public.group_whitelist OWNER TO postgres;

--
-- Name: group_whitelist_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.group_whitelist_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.group_whitelist_id_seq OWNER TO postgres;

--
-- Name: group_whitelist_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.group_whitelist_id_seq OWNED BY public.group_whitelist.id;


--
-- Name: seasons; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.seasons (
    id integer NOT NULL,
    project text NOT NULL,
    name text NOT NULL
);


ALTER TABLE public.seasons OWNER TO postgres;

--
-- Name: seasons_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.seasons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.seasons_id_seq OWNER TO postgres;

--
-- Name: seasons_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.seasons_id_seq OWNED BY public.seasons.id;


--
-- Name: user_security; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_security (
    id integer NOT NULL,
    user_id bigint,
    name text,
    phone text,
    status text DEFAULT 'pending'::text,
    reg_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    approved_by bigint,
    approved_date timestamp without time zone
);


ALTER TABLE public.user_security OWNER TO postgres;

--
-- Name: user_security_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_security_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_security_id_seq OWNER TO postgres;

--
-- Name: user_security_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_security_id_seq OWNED BY public.user_security.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id bigint NOT NULL,
    name text,
    phone text,
    datetime timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    video_index integer DEFAULT 0,
    preferred_time text DEFAULT '07:00'::text,
    last_sent text,
    is_subscribed integer DEFAULT 1,
    viewed_videos text DEFAULT '[]'::text,
    is_group integer DEFAULT 0,
    is_banned integer DEFAULT 0,
    group_id text
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: videos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.videos (
    id integer NOT NULL,
    season_id integer,
    url text NOT NULL,
    title text NOT NULL,
    "position" integer NOT NULL
);


ALTER TABLE public.videos OWNER TO postgres;

--
-- Name: videos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.videos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.videos_id_seq OWNER TO postgres;

--
-- Name: videos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.videos_id_seq OWNED BY public.videos.id;


--
-- Name: group_whitelist id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.group_whitelist ALTER COLUMN id SET DEFAULT nextval('public.group_whitelist_id_seq'::regclass);


--
-- Name: seasons id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seasons ALTER COLUMN id SET DEFAULT nextval('public.seasons_id_seq'::regclass);


--
-- Name: user_security id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_security ALTER COLUMN id SET DEFAULT nextval('public.user_security_id_seq'::regclass);


--
-- Name: videos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.videos ALTER COLUMN id SET DEFAULT nextval('public.videos_id_seq'::regclass);


--
-- Data for Name: admins; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.admins (user_id) FROM stdin;
\.


--
-- Data for Name: group_video_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.group_video_settings (chat_id, centris_enabled, centris_start_video, golden_enabled, golden_start_video, viewed_videos, is_subscribed, centris_season_id, golden_season_id, group_name, centris_viewed_videos, golden_viewed_videos, send_times) FROM stdin;
-4814911087	0	0	0	0	[]	1	\N	\N	ergfvergv	[]	[]	["08:00", "20:00"]
-1003083372899	1	1	0	0	[1]	1	14	\N	Saidbek Uchun | Centris Towers Videolari	[0, 1, 2, 3, 4]	[]	["13:47", "13:48"]
-4918182410	0	0	0	0	[]	1	\N	\N	test server	[]	[]	["08:00", "20:00"]
-4927690978	0	0	0	0	[]	1	\N	\N	testtttttttttt	[]	[]	["08:00", "20:00"]
5657091547	1	16	0	0	[]	1	18	\N	Mohirbek	[]	[]	["08:00", "20:00"]
-4852567037	0	0	0	0	[]	1	\N	\N	123test	[]	[]	["08:00", "20:00"]
-1002659691937	0	0	0	0	[]	1	\N	\N	Eventlar \\ Trio lidgen lidCon ORG	[]	[]	["08:00", "20:00"]
-4825607851	1	1	0	0	[]	1	14	\N	Saidbek Uchun | Centris Towers Videolari	[0, 1]	[]	["13:31", "13:32"]
-4980587182	1	22	1	6	[1, 26]	1	11	19	Noma'lum guruh	[22, 23, 24, 25, 26, 27, 28]	[6, 7, 8]	["15:08", "15:09", "15:10"]
-4848529394	1	1	1	1	[1]	1	14	19	Mohirbek и Centris Towers	[1, 2, 3, 4, 5, 6]	[1, 2, 3]	["08:00", "20:00"]
-4937569218	1	1	0	0	[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 26]	1	18	\N	Bot Centris towers test	[1, 2, 3, 4, 5, 6]	[]	["08:00", "20:00"]
-4905585826	1	0	1	16	[]	1	18	13	TESSSSSST	[3, 25, 26, 27, 0, 1, 2, 4]	[14, 16, 17]	["08:00", "14:00", "20:00"]
-1002223935003	0	0	1	1	[0, 17, 4, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]	0	\N	20	test bot	[]	[1, 2, 3, 4, 5, 6]	["08:00", "20:00"]
-4917794269	1	1	0	0	[0]	1	14	\N	Centris Team | Org	[0, 1, 2, 3, 4]	[]	["12:31", "12:32"]
-4867998506	0	0	0	0	[]	1	\N	\N	13e12	[]	[]	["08:00", "20:00"]
-1002802807826	0	0	0	0	[]	1	\N	\N	2w1223	[]	[]	["08:00", "20:00"]
-4620491106	0	0	0	0	[]	1	\N	\N	Bbb	[]	[]	["08:00", "20:00"]
-4911418128	0	0	0	0	[1]	0	\N	\N	Sss	[]	[]	["08:00", "20:00"]
-4809430284	0	0	0	0	[]	1	\N	\N	rwfewrger4g	[]	[]	["08:00", "20:00"]
-4876169003	0	0	0	0	[]	1	\N	\N	rfvergvgewr	[]	[]	["08:00", "20:00"]
\.


--
-- Data for Name: group_whitelist; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.group_whitelist (id, chat_id, title, status, added_date, added_by) FROM stdin;
1	-1002888574823	Qo'shilgan guruh	active	2025-08-08 20:51:02.625392	5657091547
2	-4937569218	Bot Centris towers test	active	2025-08-18 13:39:50.790604	5657091547
3	-4918182410	test server	active	2025-08-19 04:45:28.279944	5657091547
4	-4927690978	testtttttttttt	active	2025-08-19 10:28:22.50023	5657091547
5	-4905585826	TESSSSSST	active	2025-08-20 17:33:58.283661	5657091547
6	-1002223935003	test bot	active	2025-08-20 20:44:50.529881	5657091547
7	-4911418128	Bot test Centris towers	active	2025-08-21 09:48:40.228027	5657091547
8	-4848529394	Mohirbek и Centris Towers	active	2025-08-21 20:32:46.980928	5657091547
9	-4852567037	123test	active	2025-08-30 18:45:53.325994	5657091547
10	-4917794269	Centris Team | Org	active	2025-08-31 07:27:56.3768	5310261745
11	-1002659691937	Eventlar \\ Trio lidgen lidCon ORG	active	2025-08-31 08:18:12.070904	5310261745
12	-4825607851	Saidbek Uchun	active	2025-08-31 08:18:50.983257	5310261745
13	-1003083372899	Saidbek Uchun | Centris Towers Videolari	active	2025-08-31 08:35:35.636312	5310261745
14	-4980587182	about bot	active	2025-08-31 10:06:21.995833	5657091547
\.


--
-- Data for Name: seasons; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.seasons (id, project, name) FROM stdin;
9	centris	Якинлар I Иброҳим Мамасаидов
10	centris	Яқинлар 2.0 I I Иброҳим Мамасаидов
11	centris	Яқинлар 3.0 I I Иброҳим Мамасаидов
12	golden	Ислом Мамасаидов “Golden Lake” лойиҳаси асосчиси.
13	golden	Ислом Мамасаидов “Golden Lake” лойиҳаси асосчиси I I
14	centris	Яқинлар 4.0 || Иброхим Мамасаидов
15	centris	Яқинлар 5.0 | Мақсад Мансуров y5
18	centris	Яқинлар 8 I Ташриф Centris Towers Yaqinlar 8 Tashrif y8
19	golden	Яқинлар 7 | Иброҳим Мамасаидов | Golden Lake y7
20	golden	Яқинлар 9.0 I Golden Lake Yaqinlar 9 y9
\.


--
-- Data for Name: user_security; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_security (id, user_id, name, phone, status, reg_date, approved_by, approved_date) FROM stdin;
1	5657091547	Mohirbek	+998996556503	approved	2025-08-08 20:24:45.233528	5657091547	2025-08-08 20:25:00.215106
2	40450445	Halil	821080505070	pending	2025-08-10 10:19:19.244719	\N	\N
3	8375967697	Ali	+19297001011	pending	2025-08-14 07:03:23.77654	\N	\N
4	7964581311	Samir	905033529	pending	2025-08-14 09:15:09.541889	\N	\N
6	7535690668	Zoirov azizbek	998 91 956 31 35	pending	2025-08-17 15:30:58.611617	\N	\N
7	5310261745	Ziyodulla	958544400	approved	2025-08-21 09:12:51.89706	5310261745	2025-08-21 09:13:01.643035
9	43699859	Жавохир	93.5568000	approved	2025-08-21 09:18:13.117237	5657091547	2025-08-21 09:18:57.016238
10	7570805489	Ziyodulla	958544400	approved	2025-08-21 11:39:18.960429	5657091547	2025-08-21 11:39:34.433158
8	7577910176	Mohirbek	+998996556503	approved	2025-08-21 09:17:24.883736	5657091547	2025-08-21 16:20:54.217097
11	105624699	Amina	909809809	approved	2025-08-22 12:49:38.094814	5657091547	2025-08-22 12:49:49.912881
12	1213694955	Ulug'bek	+998911871232	approved	2025-08-23 05:25:10.034533	5657091547	2025-08-23 05:25:30.601167
5	7983512278	erggvwergf	+998996556503	approved	2025-08-16 05:23:38.542834	5657091547	2025-08-23 05:40:55.210735
13	964383949	Sayyora	991754000	denied	2025-08-24 13:09:52.492455	5657091547	2025-08-24 13:25:14.594218
14	1849953640	Firdavs	+998937487750	pending	2025-08-30 11:59:19.10967	\N	\N
15	6418519368	Olloniyoz	950219887	denied	2025-08-31 10:03:07.505845	8053364577	2025-09-02 18:57:02.655787
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (user_id, name, phone, datetime, video_index, preferred_time, last_sent, is_subscribed, viewed_videos, is_group, is_banned, group_id) FROM stdin;
-4867998506	13e12	\N	2025-07-10 13:14:03.41052	0	07:00	\N	0	[]	1	1	\N
-1002802807826	2w1223	\N	2025-07-17 06:07:12.131509	0	07:00	\N	1	[]	1	0	\N
-4620491106	Bbb	\N	2025-07-17 09:58:58.951247	0	07:00	\N	0	[]	1	1	\N
-4911418128	Sss	\N	2025-07-17 09:59:46.946981	0	07:00	\N	1	[]	1	0	\N
-1002223935003	test bot	\N	2025-08-14 09:15:58.765751	0	07:00	\N	1	[]	1	0	\N
-4809430284	rwfewrger4g	\N	2025-08-16 05:23:59.241222	0	07:00	\N	1	[]	1	0	\N
-4876169003	rfvergvgewr	\N	2025-08-17 12:27:34.885464	0	07:00	\N	1	[]	1	0	\N
-4814911087	ergfvergv	\N	2025-08-17 12:49:41.959833	0	07:00	\N	1	[]	1	0	\N
-4937569218	Bot Centris towers test	\N	2025-08-18 13:39:50.788322	0	07:00	\N	1	[]	1	0	\N
-4918182410	test server	\N	2025-08-19 04:45:28.276939	0	07:00	\N	1	[]	1	0	\N
-4927690978	testtttttttttt	\N	2025-08-19 10:28:22.497986	0	07:00	\N	1	[]	1	0	\N
-4905585826	TESSSSSST	\N	2025-08-20 17:33:58.281723	0	07:00	\N	1	[]	1	0	\N
8053364577	Не указано	Не указано	2025-08-21 12:38:18.279411	0	09:00	\N	1	[]	0	0	-4911418128
-4848529394	Mohirbek и Centris Towers	\N	2025-08-21 20:32:46.97834	0	07:00	\N	1	[]	1	0	\N
-4852567037	123test	\N	2025-08-30 18:45:53.323963	0	07:00	\N	1	[]	1	0	\N
-1002659691937	Eventlar \\ Trio lidgen lidCon ORG	\N	2025-08-31 08:18:12.069073	0	07:00	\N	1	[]	1	0	\N
5310261745	Не указано	Не указано	2025-08-31 08:30:49.910782	0	09:00	\N	1	[]	0	0	-4825607851
-4917794269	Centris Team | Org	\N	2025-08-31 07:27:56.375418	0	07:00	\N	1	[]	1	0	\N
-4825607851	Saidbek Uchun | Centris Towers Videolari	\N	2025-08-31 08:18:50.98183	0	07:00	\N	1	[]	1	0	\N
-1003083372899	Saidbek Uchun | Centris Towers Videolari	\N	2025-08-31 08:35:35.634843	0	07:00	\N	1	[]	1	0	\N
5657091547	Mohirbek	998996556503	2025-07-10 11:59:25.341091	0	07:00	\N	1	[]	0	0	\N
-4980587182	about bot	\N	2025-08-31 10:06:21.994093	0	07:00	\N	1	[]	1	0	\N
\.


--
-- Data for Name: videos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.videos (id, season_id, url, title, "position") FROM stdin;
137	9	https://t.me/c/2550852551/543	1. Centris Towers’даги лобби	0
138	9	https://t.me/c/2550852551/544	2. Хизмат кўрсатиш харажатларини камайтириш бўйича режалар	1
139	9	https://t.me/c/2550852551/545	3. Таъсир қилувчи шахслар ўзимизда I Марказдаги ер нархи ўсиши тезлашган	2
140	9	https://t.me/c/2550852551/546	4. Centris Towers - қўшимча қулайликлари	3
141	9	https://t.me/c/2550852551/547	5. Бино қачон кўринади	4
142	9	https://t.me/c/2550852551/548	6. Парковка сотилмайди	5
143	9	https://t.me/c/2550852551/549	7. Centris Towers — Муваффақият Маркази	6
144	9	https://t.me/c/2550852551/550	8. Охирги пулига олинмаган	7
145	9	https://t.me/c/2550852551/551	9. Инвестиция хавфсизлиги	8
146	9	https://t.me/c/2550852551/552	10. Қурилиш битишига таъсир қилувчи омиллар	9
147	9	https://t.me/c/2550852551/553	11. Манга қўшниларим муҳим	10
148	9	https://t.me/c/2550852551/554	12. Бизга қайси сегмент қизиқ	11
149	9	https://t.me/c/2550852551/555	13. Centris Towers ғояси	12
150	9	https://t.me/c/2550852551/556	14. Centris Towers қулайликлари ва инвестиция бўйича хавфсизлиги	13
151	9	https://t.me/c/2550852551/557	15. Centris Towers — Муваффақият Маркази (Full)	14
152	10	https://t.me/c/2550852551/559	Келажакни инобатга олган қулай локатсия	0
153	10	https://t.me/c/2550852551/560	Худуд бўйича жойлашув ва нархлар.	1
154	10	https://t.me/c/2550852551/561	Парковка масаласи ва тарифлари	2
155	10	https://t.me/c/2550852551/562	Хавфсизлик бўйича талабларга жавобимиз	3
156	10	https://t.me/c/2550852551/563	Меҳмонлар учун қулайликлар	4
157	10	https://t.me/c/2550852551/564	Макетдаги бино қани деб қолмаймизми?	5
158	10	https://t.me/c/2550852551/565	Қарзга олгандан кўра, олмаслик яхшироқ.	6
159	10	https://t.me/c/2550852551/566	“Centris Towers” қандай ва кимлар учун.	7
160	10	https://t.me/c/2550852551/567	Ўхшамай қолса пулингиз қайтарилади	8
161	10	https://t.me/c/2550852551/568	Бинонинг ташқи худуди.	9
162	10	https://t.me/c/2550852551/569	Фитнес ва автосалоннинг боғлиқлиги.	10
163	10	https://t.me/c/2550852551/570	Аёллар учун ажратилган зона	11
164	10	https://t.me/c/2550852551/571	Нарх сиёсатининг муҳимлиги.	12
165	10	https://t.me/c/2550852551/572	«Вид» муҳим деб билганлар  учун таклиф.	13
166	10	https://t.me/c/2550852551/573	Сотиш учун олаётганларга тавсия.	14
167	10	https://t.me/c/2550852551/574	Эвакуация кучли ўйланилган.	15
168	10	https://t.me/c/2550852551/575	Бизнес центр қуриш осонмас…	16
169	10	https://t.me/c/2550852551/576	100% тўлов қилишнинг чегирмаси.	17
170	10	https://t.me/c/2550852551/577	Чет эл фуқаролари ҳам олса бўладими?	18
171	10	https://t.me/c/2550852551/578	Тўлиқ кўрсатув…	19
172	11	https://t.me/c/2550852551/612	"Centris Towers" билан ҳамкорлик шартлари	0
173	11	https://t.me/c/2550852551/613	Ижара нархлари	1
174	11	https://t.me/c/2550852551/614	"Centris Towers" нинг ташқи тузилиши	2
175	11	https://t.me/c/2550852551/615	Энг оммабоп муаммонинг ечими.	3
176	11	https://t.me/c/2550852551/616	Қаҳвахона ёки кафе учун идеал жой	4
177	11	https://t.me/c/2550852551/617	Биздаги 4 хил уникал ресторан	5
178	11	https://t.me/c/2550852551/618	"Centris Towers" нинг бошқалардан фарқи.	6
179	11	https://t.me/c/2550852551/619	Қаҳва бурчак (Coffee Corner) учун таклиф	7
180	11	https://t.me/c/2550852551/620	Бино қурилиши қачон тугайди?	8
181	11	https://t.me/c/2550852551/621	Саволларга жавоб олиш учун кимга мурожаат қилиш керак?	9
182	11	https://t.me/c/2550852551/622	Бизга кимлар қизиқ эмас?	10
183	11	https://t.me/c/2550852551/623	Ёш болалар учун ўйин майдони бўладими?	11
184	11	https://t.me/c/2550852551/624	Автосалон очадиганларга учун имконият.	12
185	11	https://t.me/c/2550852551/625	Бино фасади учун режалар	13
186	11	https://t.me/c/2550852551/626	Аёллар учун қулайликлар	14
187	11	https://t.me/c/2550852551/627	''Co-working" зоналари учун ажратилган имкониятлар	15
188	11	https://t.me/c/2550852551/628	Ижара шартномаси долларда бўладими ёки сўмда?	16
189	11	https://t.me/c/2550852551/629	Нималар мумкин эмас?	17
190	11	https://t.me/c/2550852551/630	Пул оқимида хавфлар борми?	18
191	11	https://t.me/c/2550852551/631	Шартнома учун кимлар билан келишиш керак?	19
192	11	https://t.me/c/2550852551/632	Қандай суғурта (страховка) билан таъминлайди?	20
193	11	https://t.me/c/2550852551/633	Имконият бўлмай қолса, тўланган пуллар нима бўлади?	21
194	11	https://t.me/c/2550852551/634	Таклиф нима учун камаяди?	22
195	11	https://t.me/c/2550852551/635	Нима учун тиллага эмас, кўчмас мулкка пул тиккан маъқул?	23
196	11	https://t.me/c/2550852551/636	"Centris Towers" девелопер сифатида яқин келажакдаги қурилиш режалари ҳақида фикрингиз.	24
197	11	https://t.me/c/2550852551/637	ТОП-3 брендлар қаторида жой олишимиз мумкинми?	25
198	11	https://t.me/c/2550852551/638	"Centris Towers" расман қачон очилиши мумкин?	26
199	11	https://t.me/c/2550852551/639	Лифтлар билан боғлиқ қулайликлар	27
200	11	https://t.me/c/2550852551/640	Чет элга сармоя киритиш керакми ёки Ўзбекистонга?	28
201	11	https://t.me/c/2550852551/641	Дубай ва Озарбайжонга пул тикиш тўғрими?	29
202	11	https://t.me/c/2550852551/642	Тўлиқ кўрсатув	30
203	12	https://t.me/c/2550852551/648	Кириш ва хавфсизлик тизими	0
204	12	https://t.me/c/2550852551/649	Лойихадаги блоклар ва хонадонлар	1
205	12	https://t.me/c/2550852551/650	Аксарият турар жойларда бундай қулайликлар йўқ…	2
206	12	https://t.me/c/2550852551/651	Ҳовли яхшироқми?	3
207	12	https://t.me/c/2550852551/652	Барака топсин дейишларини хоҳлаймиз!	4
208	12	https://t.me/c/2550852551/653	Сотув учун	5
209	12	https://t.me/c/2550852551/654	Бунақаси ҳали бизда бўлмаган	6
210	12	https://t.me/c/2550852551/655	Премиум, комфорт, стандарт ёки эконом	7
211	12	https://t.me/c/2550852551/656	Ташқи интерьер	8
212	12	https://t.me/c/2550852551/657	Блоклар бўйича қулайликлар	9
213	12	https://t.me/c/2550852551/658	Қадриятимизга тўғри келмайди	10
214	12	https://t.me/c/2550852551/659	Сотув учун керакли ҳужжатлар ва жиҳатлар	11
215	12	https://t.me/c/2550852551/660	Инвесторлар учун	12
216	12	https://t.me/c/2550852551/661	Тўлов шакли	13
217	12	https://t.me/c/2550852551/662	Тўлиқ кўрсатув	14
218	13	https://t.me/c/2550852551/668	Олтинкўл лойиҳасининг бошланиш тарихи	0
219	13	https://t.me/c/2550852551/669	Лойиҳанинг энг кучли тарафи	1
220	13	https://t.me/c/2550852551/670	Лойиҳанинг муҳим жиҳатлари	2
221	13	https://t.me/c/2550852551/671	Олтинкўлнинг ҳудудий тузулиши	3
222	13	https://t.me/c/2550852551/672	Хавфсизлик қанчалик таъминланган?	4
223	13	https://t.me/c/2550852551/673	Ижтимоий жиҳатдан ёш болалилар учун қулайликлар	5
224	13	https://t.me/c/2550852551/674	Ҳудуддан чиқмасдан дўконлардан фойдаланиш	6
225	13	https://t.me/c/2550852551/675	Баландлиги ҳовлиникидай бўлган хонадонлар.	7
226	13	https://t.me/c/2550852551/676	Қадриятларга мос услубда қурилган турар жой	8
227	13	https://t.me/c/2550852551/677	Кўнгил очар манзиллар	9
228	13	https://t.me/c/2550852551/678	Парковка билан муаммосиз ҳудуд	10
229	13	https://t.me/c/2550852551/679	Экологик муаммоларга ечим	11
230	13	https://t.me/c/2550852551/680	Энг кўп эътибор ва вақтимизни олган омил	12
231	13	https://t.me/c/2550852551/681	Нечта блок ва нечта бинодан иборат?	13
232	13	https://t.me/c/2550852551/682	Инвестор фақат пулни ўйлайди!	14
233	13	https://t.me/c/2550852551/683	Лойиҳа қачон битади?	15
234	13	https://t.me/c/2550852551/684	Лойиҳа мақсади ва нархи	16
235	13	https://t.me/c/2550852551/685	Иситиш тизими қандай?	17
236	13	https://t.me/c/2550852551/686	Домнинг конкуренти бу машина!	18
237	13	https://t.me/c/2550852551/687	Тўлиқ кўрсатув	19
238	14	https://t.me/c/2550852551/697	Бино локацияси ва тузилиши	0
239	14	https://t.me/c/2550852551/698	Бино ичидаги қулайликлар	1
240	14	https://t.me/c/2550852551/699	Парковка ва унинг имкониятлари	2
241	14	https://t.me/c/2550852551/700	Халқаро компанияларга ҳам очиқмиз	3
242	14	https://t.me/c/2550852551/701	Co-working марказлари берадиган имкониятлар	4
243	14	https://t.me/c/2550852551/702	Бино қаватлари бўйича қилинган режалар	5
244	14	https://t.me/c/2550852551/703	Бино қурилиши қачон тугайди ва нархлари қандай бўлади?	6
245	14	https://t.me/c/2550852551/704	Сотиб олганимдан кейин қачондан ва қандай ишлата оламан?	7
246	14	https://t.me/c/2550852551/705	Бинодаги қўшимча шароитлар	8
247	14	https://t.me/c/2550852551/706	Бино aниқ белгиланган вақтда битадими?	9
248	14	https://t.me/c/2550852551/707	Инвестор бўлсам ютқазмайманми?	10
249	14	https://t.me/c/2550852551/708	Парковка сотиладими?	11
250	14	https://t.me/c/2550852551/709	Хавфсизликка жавоб бериладими?	12
251	14	https://t.me/c/2550852551/710	Қайси машҳур бинога ўхшайди?	13
252	14	https://t.me/c/2550852551/711	Тўлиқ кўрсатув	14
253	15	https://t.me/c/2550852551/713	Нимага айнан Centris Towers?	0
254	15	https://t.me/c/2550852551/714	Локациядаги афзаллик.	1
255	15	https://t.me/c/2550852551/715	Мижозларимизнинг асосий мақсади.	2
256	15	https://t.me/c/2550852551/716	Корпус бўйича бино тузилиши	3
257	15	https://t.me/c/2550852551/717	Қонун бўйича ёндашамиз.	4
258	15	https://t.me/c/2550852551/718	Парковка сотилмаслигининг сабаби	5
259	15	https://t.me/c/2550852551/719	Ишонч учун…	6
260	15	https://t.me/c/2550852551/720	Йиллик мақсадлар	7
261	15	https://t.me/c/2550852551/721	Хавфсизлик таъминланади!	8
262	15	https://t.me/c/2550852551/722	“A” класс ҳақида.	9
263	15	https://t.me/c/2550852551/723	Қурилишдаги материаллар.	10
264	15	https://t.me/c/2550852551/724	Кам даромад кўрсакда натижа зўр бўлсин.	11
265	15	https://t.me/c/2550852551/725	Бино террасаси.	12
266	15	https://t.me/c/2550852551/726	Парковка сиғими.	13
267	15	https://t.me/c/2550852551/727	Келишув нархи: Доллар ёки сўм?	14
268	15	https://t.me/c/2550852551/728	Энг уникал қулайликлар.	15
269	15	https://t.me/c/2550852551/729	Бепул хизматлар борми?	16
270	15	https://t.me/c/2550852551/730	Ҳужжатлар билан ишлаш тартиби.	17
271	15	https://t.me/c/2550852551/731	Ижара ва сотув.	18
272	15	https://t.me/c/2550852551/732	Нимага айнан “Koç Construction” танланди?	19
273	15	https://t.me/c/2550852551/733	Ички бошқарув	20
274	15	https://t.me/c/2550852551/734	Centris брендлари.	21
275	15	https://t.me/c/2550852551/735	Энг муҳими бу локация	22
276	15	https://t.me/c/2550852551/736	Инвесторлар психологияси.	23
277	15	https://t.me/c/2550852551/737	Нима учун айнан муваффақият маркази?	24
278	15	https://t.me/c/2550852551/738	Инвесторлар хотиржам бўлиши мумкин!	25
279	15	https://t.me/c/2550852551/739	Бугун вақти!	26
280	15	https://t.me/c/2550852551/740	Тўлиқ кўрсатув	27
325	18	https://t.me/c/2550852551/742	Қурилишдаги ўзига хос жиҳатлар ва қозиқларнинг аҳамияти	0
326	18	https://t.me/c/2550852551/743	A, B, C Tower'лар ва фасад ишлари ҳақида	1
327	18	https://t.me/c/2550852551/744	"Centris Towers"нинг жойлашуви	2
328	18	https://t.me/c/2550852551/745	Фасад ишларида ҳисобга олинган омиллар	3
329	18	https://t.me/c/2550852551/746	1-қаватдаги майдонлар ҳақида	4
330	18	https://t.me/c/2550852551/747	Автотураргоҳлар ва ақлли вентиляция тизими	5
331	18	https://t.me/c/2550852551/748	"Centris Towers"даги ақлли лифт тизими	6
332	18	https://t.me/c/2550852551/749	Қурилишда ишлатилаётган материаллар	7
333	18	https://t.me/c/2550852551/750	Ҳамкорларга 2-қават майдонлари бўйича таклифлар	8
334	18	https://t.me/c/2550852551/751	3-қаватдаги террасалар	9
335	18	https://t.me/c/2550852551/752	Синовдан ўтказилаётган ойналар	10
336	18	https://t.me/c/2550852551/753	D-E блокдан пойтахтнинг кўриниши	11
337	18	https://t.me/c/2550852551/754	Фасад ойналари ва уларнинг афзалликлари ҳақида	12
338	18	https://t.me/c/2550852551/755	Яшиллик билан ўралган "Centris Towers"	13
339	18	https://t.me/c/2550852551/756	Фасад ойнаси ҳақида техник тушунтириш	14
340	18	https://t.me/c/2550852551/757	Якуний қисм	15
341	19	https://t.me/c/2550852551/769	Лойиҳа жойлашуви ҳақида ҳамда бошланғич таассуротлар ва атроф-муҳит	0
342	19	https://t.me/c/2550852551/770	Ташқи кўриниш ва бино дизайни	1
343	19	https://t.me/c/2550852551/771	Ички кўриниши: хона ва жиҳозлар	2
344	19	https://t.me/c/2550852551/772	Ички коммуникация сифати, тозалик, балкон манзараси.	3
345	19	https://t.me/c/2550852551/773	Хавфсизлик, лифт ва умумий қулайликлар	4
346	19	https://t.me/c/2550852551/774	Болалар майдони, авто тураргоҳ ва яшил ҳудуд	5
347	19	https://t.me/c/2550852551/775	Нархлар, хизматлар ва ҳужжатлар	6
348	19	https://t.me/c/2550852551/776	Нима учун шу жойни танлаши керак	7
349	19	https://t.me/c/2550852551/777	Тўлиқ кўрсатув	8
350	20	https://t.me/c/2550852551/779	"Golden Lake" жойлашуви ва майдони	0
351	20	https://t.me/c/2550852551/780	"Golden Lake"нинг бошқа лойиҳалардан афзаллиги	1
352	20	https://t.me/c/2550852551/781	Ҳозирги кундаги нархлар ва инвестиция	2
353	20	https://t.me/c/2550852551/782	Лойиҳа қурилиши қайси компанияга топширилган?	3
354	20	https://t.me/c/2550852551/783	ROI кўрсаткичлари	4
355	20	https://t.me/c/2550852551/784	"Golden Lake"га инвестиция қилишнинг афзалликлари	5
356	20	https://t.me/c/2550852551/785	Комфорт плюс даражада бўлишининг сабаблари	6
357	20	https://t.me/c/2550852551/786	"Golden Lake" концепцияси ҳақида	7
358	20	https://t.me/c/2550852551/787	"Golden Lake" даги қулайликлар ҳақида	8
359	20	https://t.me/c/2550852551/788	Қурилиш муддати	9
360	20	https://t.me/c/2550852551/789	Харидорларга тавсиялар	10
361	20	https://t.me/c/2550852551/790	Компаниялар учун қулай таклифлар	11
362	20	https://t.me/c/2550852551/791	"Фурқат" боғи ва "Хотиржамлик маскани" ҳақида	12
363	20	https://t.me/c/2550852551/792	Уникал қулайликлар ҳақида	13
364	20	https://t.me/c/2550852551/793	24/7 қўриқланадиган ҳудуд	14
365	20	https://t.me/c/2550852551/794	"Golden Lake" даги блоклар ва showroom’ларнинг очилиш вақти	15
366	20	https://t.me/c/2550852551/795	"Golden Lake" даги пентхауслар ҳақида	16
367	20	https://t.me/c/2550852551/796	Хонадонларнинг мижозларга топширилиш ҳолати	17
368	20	https://t.me/c/2550852551/797	Қурилишда ишлатилаётган материаллар ва лифтлар ҳақида	18
369	20	https://t.me/c/2550852551/798	Қурилишда ишлатилаётган материаллар ва лифтлар ҳақида	19
370	20	https://t.me/c/2550852551/799	Тўлов турлари ва чегирмалар ҳақида	20
371	20	https://t.me/c/2550852551/800	Тўлиқ кўрсатув	21
\.


--
-- Name: group_whitelist_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.group_whitelist_id_seq', 14, true);


--
-- Name: seasons_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.seasons_id_seq', 21, true);


--
-- Name: user_security_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_security_id_seq', 15, true);


--
-- Name: videos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.videos_id_seq', 387, true);


--
-- Name: admins admins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_pkey PRIMARY KEY (user_id);


--
-- Name: group_video_settings group_video_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.group_video_settings
    ADD CONSTRAINT group_video_settings_pkey PRIMARY KEY (chat_id);


--
-- Name: group_whitelist group_whitelist_chat_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.group_whitelist
    ADD CONSTRAINT group_whitelist_chat_id_key UNIQUE (chat_id);


--
-- Name: group_whitelist group_whitelist_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.group_whitelist
    ADD CONSTRAINT group_whitelist_pkey PRIMARY KEY (id);


--
-- Name: seasons seasons_pkey1; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seasons
    ADD CONSTRAINT seasons_pkey1 PRIMARY KEY (id);


--
-- Name: user_security user_security_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_security
    ADD CONSTRAINT user_security_pkey PRIMARY KEY (id);


--
-- Name: user_security user_security_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_security
    ADD CONSTRAINT user_security_user_id_key UNIQUE (user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: videos videos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.videos
    ADD CONSTRAINT videos_pkey PRIMARY KEY (id);


--
-- Name: videos videos_season_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.videos
    ADD CONSTRAINT videos_season_id_fkey FOREIGN KEY (season_id) REFERENCES public.seasons(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

