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

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: centris
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO centris;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: centris
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: admins; Type: TABLE; Schema: public; Owner: centris
--

CREATE TABLE public.admins (
    user_id bigint NOT NULL,
    name text,
    added_by bigint,
    added_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.admins OWNER TO centris;

--
-- Name: db_version; Type: TABLE; Schema: public; Owner: centris
--

CREATE TABLE public.db_version (
    version integer DEFAULT 1 NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.db_version OWNER TO centris;

--
-- Name: group_video_settings; Type: TABLE; Schema: public; Owner: centris
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


ALTER TABLE public.group_video_settings OWNER TO centris;

--
-- Name: group_video_settings_backup; Type: TABLE; Schema: public; Owner: centris
--

CREATE TABLE public.group_video_settings_backup (
    chat_id text,
    centris_enabled integer,
    centris_season text,
    centris_start_season_id integer,
    centris_start_video integer,
    golden_enabled integer,
    golden_start_season_id integer,
    golden_start_video integer,
    viewed_videos text,
    is_subscribed integer
);


ALTER TABLE public.group_video_settings_backup OWNER TO centris;

--
-- Name: group_whitelist; Type: TABLE; Schema: public; Owner: centris
--

CREATE TABLE public.group_whitelist (
    id integer NOT NULL,
    chat_id bigint,
    title text,
    status text DEFAULT 'active'::text,
    added_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    added_by bigint
);


ALTER TABLE public.group_whitelist OWNER TO centris;

--
-- Name: group_whitelist_id_seq; Type: SEQUENCE; Schema: public; Owner: centris
--

CREATE SEQUENCE public.group_whitelist_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.group_whitelist_id_seq OWNER TO centris;

--
-- Name: group_whitelist_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: centris
--

ALTER SEQUENCE public.group_whitelist_id_seq OWNED BY public.group_whitelist.id;


--
-- Name: seasons; Type: TABLE; Schema: public; Owner: centris
--

CREATE TABLE public.seasons (
    id integer NOT NULL,
    project text NOT NULL,
    name text NOT NULL
);


ALTER TABLE public.seasons OWNER TO centris;

--
-- Name: seasons_id_seq; Type: SEQUENCE; Schema: public; Owner: centris
--

CREATE SEQUENCE public.seasons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.seasons_id_seq OWNER TO centris;

--
-- Name: seasons_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: centris
--

ALTER SEQUENCE public.seasons_id_seq OWNED BY public.seasons.id;


--
-- Name: settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.settings (
    key text NOT NULL,
    value text
);


ALTER TABLE public.settings OWNER TO postgres;

--
-- Name: support; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.support (
    id integer NOT NULL,
    user_id bigint,
    message text,
    datetime timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.support OWNER TO postgres;

--
-- Name: support_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.support_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.support_id_seq OWNER TO postgres;

--
-- Name: support_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.support_id_seq OWNED BY public.support.id;


--
-- Name: user_security; Type: TABLE; Schema: public; Owner: centris
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


ALTER TABLE public.user_security OWNER TO centris;

--
-- Name: user_security_id_seq; Type: SEQUENCE; Schema: public; Owner: centris
--

CREATE SEQUENCE public.user_security_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_security_id_seq OWNER TO centris;

--
-- Name: user_security_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: centris
--

ALTER SEQUENCE public.user_security_id_seq OWNED BY public.user_security.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: centris
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


ALTER TABLE public.users OWNER TO centris;

--
-- Name: videos; Type: TABLE; Schema: public; Owner: centris
--

CREATE TABLE public.videos (
    id integer NOT NULL,
    season_id integer,
    url text NOT NULL,
    title text NOT NULL,
    "position" integer NOT NULL
);


ALTER TABLE public.videos OWNER TO centris;

--
-- Name: videos_id_seq; Type: SEQUENCE; Schema: public; Owner: centris
--

CREATE SEQUENCE public.videos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.videos_id_seq OWNER TO centris;

--
-- Name: videos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: centris
--

ALTER SEQUENCE public.videos_id_seq OWNED BY public.videos.id;


--
-- Name: group_whitelist id; Type: DEFAULT; Schema: public; Owner: centris
--

ALTER TABLE ONLY public.group_whitelist ALTER COLUMN id SET DEFAULT nextval('public.group_whitelist_id_seq'::regclass);


--
-- Name: seasons id; Type: DEFAULT; Schema: public; Owner: centris
--

ALTER TABLE ONLY public.seasons ALTER COLUMN id SET DEFAULT nextval('public.seasons_id_seq'::regclass);


--
-- Name: support id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.support ALTER COLUMN id SET DEFAULT nextval('public.support_id_seq'::regclass);


--
-- Name: user_security id; Type: DEFAULT; Schema: public; Owner: centris
--

ALTER TABLE ONLY public.user_security ALTER COLUMN id SET DEFAULT nextval('public.user_security_id_seq'::regclass);


--
-- Name: videos id; Type: DEFAULT; Schema: public; Owner: centris
--

ALTER TABLE ONLY public.videos ALTER COLUMN id SET DEFAULT nextval('public.videos_id_seq'::regclass);


--
-- Data for Name: admins; Type: TABLE DATA; Schema: public; Owner: centris
--

COPY public.admins (user_id, name, added_by, added_date) FROM stdin;
5657091547	Super Admin	0	2025-09-03 09:05:52.751905
5310261745	Super Admin	0	2025-09-03 09:05:52.754815
8053364577	Super Admin	\N	2025-09-03 13:45:39.641831
\.


--
-- Data for Name: db_version; Type: TABLE DATA; Schema: public; Owner: centris
--

COPY public.db_version (version, updated_at) FROM stdin;
1	2025-08-17 21:46:49.496791
2	2025-08-17 21:46:49.52025
3	2025-08-17 21:46:49.524434
\.


--
-- Data for Name: group_video_settings; Type: TABLE DATA; Schema: public; Owner: centris
--

COPY public.group_video_settings (chat_id, centris_enabled, centris_start_video, golden_enabled, golden_start_video, viewed_videos, is_subscribed, centris_season_id, golden_season_id, group_name, centris_viewed_videos, golden_viewed_videos, send_times) FROM stdin;
5657091547	1	0	0	0	[]	1	4	\N	Mohirbek	[]	[]	["08:00", "20:00"]
-4876956827	1	0	1	0	[]	1	3	5	refgvergv	[]	[]	["00:25", "15:00"]
-4916726640	0	0	0	0	[]	1	\N	\N	rfvgetfbetrf	[]	[]	["08:00", "20:00"]
-4964612772	1	0	0	0	[]	1	3	\N	wefwergvewrg	[]	[]	["08:00", "20:00"]
-4980133706	1	4	1	4	[]	1	1	5	test	[4, 5]	[]	["20:58", "20:59"]
-4843623445	0	0	0	0	[]	1	\N	\N	test 2	[]	[]	["08:00", "20:00"]
-4698018786	0	0	0	0	[]	1	\N	\N	укамцука	[]	[]	["08:00", "20:00"]
-4801880668	1	0	0	0	[]	1	4	\N	test 43	[]	[]	["08:00", "20:00"]
-4910088668	1	0	0	0	[]	1	4	\N	rfvgerbb	[]	[]	["08:00", "20:00"]
-4982904251	1	9	1	0	[]	1	2	7	test 111111	[]	[]	["08:00", "20:00"]
-4805050234	1	0	1	0	[]	1	3	5	rfvrffergg	[]	[]	["08:00", "20:00"]
-4898539004	1	0	1	0	[]	1	3	7	1111111111111	[]	[]	["08:00", "20:00"]
-4945967161	0	0	1	6	[]	1	\N	5	111111111111111122222222	[]	[6]	["09:00", "21:00"]
-4903451090	1	9	1	8	[]	1	1	5	testlar123	[10, 11]	[]	["08:00", "14:00", "20:00"]
-4874798023	0	0	0	0	[]	1	\N	\N	efrswv	[]	[]	["08:00", "20:00"]
-4951943600	0	0	0	0	[]	1	\N	\N	Hdbdbdjdn	[]	[]	["08:00", "20:00"]
-4899838950	0	0	0	0	[]	1	\N	\N	Gggggggg	[]	[]	["08:00", "20:00"]
\.


--
-- Data for Name: group_video_settings_backup; Type: TABLE DATA; Schema: public; Owner: centris
--

COPY public.group_video_settings_backup (chat_id, centris_enabled, centris_season, centris_start_season_id, centris_start_video, golden_enabled, golden_start_season_id, golden_start_video, viewed_videos, is_subscribed) FROM stdin;
5657091547	1	1	1	9	0	\N	0	[]	1
\.


--
-- Data for Name: group_whitelist; Type: TABLE DATA; Schema: public; Owner: centris
--

COPY public.group_whitelist (id, chat_id, title, status, added_date, added_by) FROM stdin;
1	-4876956827	refgvergv	active	2025-08-18 09:57:46.475785	5657091547
2	-4916726640	rfvgetfbetrf	active	2025-08-18 09:57:46.475785	5657091547
3	-4964612772	wefwergvewrg	active	2025-08-18 09:57:46.475785	5657091547
4	-4980133706	test	active	2025-08-18 10:00:27.282527	5657091547
5	-4698018786	укамцука	active	2025-08-18 10:05:59.571816	7983512278
7	-4910088668	rfvgerbb	active	2025-08-18 11:03:34.199901	7577910176
8	-4982904251	test 111111	active	2025-08-18 11:09:22.154033	7983512278
9	-4805050234	rfvrffergg	active	2025-08-18 11:16:42.209634	5657091547
12	-4898539004	1111111111111	active	2025-08-19 08:57:15.185917	5657091547
13	-4945967161	111111111111111122222222	active	2025-08-19 09:37:20.431908	5657091547
6	-4801880668	test 43	active	2025-08-20 22:57:10.399893	5657091547
18	-4903451090	testlar123	active	2025-08-31 14:33:26.898471	5657091547
19	-4874798023	efrswv	active	2025-09-03 00:36:17.682336	7983512278
20	-4951943600	Hdbdbdjdn	active	2025-09-03 21:09:03.921263	8053364577
21	-4899838950	Gggggggg	active	2025-09-03 21:10:17.233933	8053364577
\.


--
-- Data for Name: seasons; Type: TABLE DATA; Schema: public; Owner: centris
--

COPY public.seasons (id, project, name) FROM stdin;
1	centris	амкпуевыкапму
2	centris	44efgver
3	centris	newssssssssss
4	centris	testlar
5	golden	tesssssssstttttttttttt
6	centris	tesssssssssstttttt
7	golden	1111111
8	centris	test 1234125
9	golden	https://t.me/c/2550852551/543\nhttps://t.me/c/2550852551/544\nhttps://t.me/c/2550852551/545\nhttps://t.me/c/2550852551/546\nhttps://t.me/c/2550852551/547\nhttps://t.me/c/2550852551/548\nhttps://t.me/c/2550852551/549\nhttps://t.me/c/2550852551/550\nhttps://t.me/c/2550852551/551\nhttps://t.me/c/2550852551/552\nhttps://t.me/c/2550852551/553\nhttps://t.me/c/2550852551/554\nhttps://t.me/c/2550852551/555\nhttps://t.me/c/2550852551/556\nhttps://t.me/c/2550852551/557
\.


--
-- Data for Name: settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.settings (key, value) FROM stdin;
\.


--
-- Data for Name: support; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.support (id, user_id, message, datetime) FROM stdin;
\.


--
-- Data for Name: user_security; Type: TABLE DATA; Schema: public; Owner: centris
--

COPY public.user_security (id, user_id, name, phone, status, reg_date, approved_by, approved_date) FROM stdin;
4	5657091547	Mohirberk	+998991234523	approved	2025-08-18 11:22:58.391715	5657091547	2025-08-18 11:23:00.719339
5	7577910176	efcdveds	+998123234132	pending	2025-08-18 11:23:26.581579	\N	\N
6	7983512278	Mohirbek	+998996556503	approved	2025-08-20 23:17:52.97227	5657091547	2025-08-20 23:17:56.743948
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: centris
--

COPY public.users (user_id, name, phone, datetime, video_index, preferred_time, last_sent, is_subscribed, viewed_videos, is_group, is_banned, group_id) FROM stdin;
-4876956827	refgvergv	\N	2025-08-18 00:14:39.009837	0	07:00	\N	1	[]	1	0	\N
-4916726640	rfvgetfbetrf	\N	2025-08-18 00:21:29.190813	0	07:00	\N	1	[]	1	0	\N
-4964612772	wefwergvewrg	\N	2025-08-18 00:22:39.638812	0	07:00	\N	1	[]	1	0	\N
-4980133706	test	\N	2025-08-18 10:00:26.653945	0	07:00	\N	1	[]	1	0	\N
-4843623445	test 2	\N	2025-08-18 10:01:04.57276	0	07:00	\N	1	[]	1	0	\N
-4698018786	укамцука	\N	2025-08-18 10:05:59.52817	0	07:00	\N	1	[]	1	0	\N
-4801880668	test 43	\N	2025-08-18 11:03:14.688153	0	07:00	\N	1	[]	1	0	\N
-4910088668	rfvgerbb	\N	2025-08-18 11:03:34.187142	0	07:00	\N	1	[]	1	0	\N
-4982904251	test 111111	\N	2025-08-18 11:09:22.140045	0	07:00	\N	1	[]	1	0	\N
-4805050234	rfvrffergg	\N	2025-08-18 11:16:42.195525	0	07:00	\N	1	[]	1	0	\N
-4898539004	1111111111111	\N	2025-08-19 08:57:15.172062	0	07:00	\N	1	[]	1	0	\N
-4945967161	111111111111111122222222	\N	2025-08-19 09:37:20.417253	0	07:00	\N	1	[]	1	0	\N
5657091547	Mohirbek	Не указано	2025-08-18 21:36:37.175805	0	09:00	\N	1	[]	0	0	-4937569218
-4903451090	testlar123	\N	2025-08-31 14:33:26.858792	0	07:00	\N	1	[]	1	0	\N
-4874798023	efrswv	\N	2025-09-03 00:36:17.669125	0	07:00	\N	1	[]	1	0	\N
7983512278	Не указано	Не указано	2025-09-03 00:36:33.329148	0	09:00	\N	1	[]	0	0	-4874798023
-4951943600	Hdbdbdjdn	\N	2025-09-03 21:09:03.916785	0	07:00	\N	1	[]	1	0	\N
8053364577	Не указано	Не указано	2025-09-03 21:09:11.029279	0	09:00	\N	1	[]	0	0	-4951943600
-4899838950	Gggggggg	\N	2025-09-03 21:10:17.207088	0	07:00	\N	1	[]	1	0	\N
\.


--
-- Data for Name: videos; Type: TABLE DATA; Schema: public; Owner: centris
--

COPY public.videos (id, season_id, url, title, "position") FROM stdin;
1	1	https://t.me/c/2550852551/543	1. Centris Towers’даги лобби	0
2	1	https://t.me/c/2550852551/544	2. Хизмат кўрсатиш харажатларини камайтириш бўйича режалар	1
3	1	https://t.me/c/2550852551/545	3. Таъсир қилувчи шахслар ўзимизда I Марказдаги ер нархи ўсиши тезлашган	2
4	1	https://t.me/c/2550852551/546	4. Centris Towers - қўшимча қулайликлари	3
5	1	https://t.me/c/2550852551/547	5. Бино қачон кўринади	4
6	1	https://t.me/c/2550852551/548	6. Парковка сотилмайди	5
7	1	https://t.me/c/2550852551/549	7. Centris Towers — Муваффақият Маркази	6
8	1	https://t.me/c/2550852551/550	8. Охирги пулига олинмаган	7
9	1	https://t.me/c/2550852551/551	9. Инвестиция хавфсизлиги	8
10	1	https://t.me/c/2550852551/552	10. Қурилиш битишига таъсир қилувчи омиллар	9
11	1	https://t.me/c/2550852551/553	11. Манга қўшниларим муҳим	10
12	1	https://t.me/c/2550852551/554	12. Бизга қайси сегмент қизиқ	11
13	1	https://t.me/c/2550852551/555	13. Centris Towers ғояси	12
14	1	https://t.me/c/2550852551/556	14. Centris Towers қулайликлари ва инвестиция бўйича хавфсизлиги	13
15	1	https://t.me/c/2550852551/557	15. Centris Towers — Муваффақият Маркази (Full)	14
16	2	https://t.me/c/2550852551/543	1. Centris Towers’даги лобби	0
17	2	https://t.me/c/2550852551/544	2. Хизмат кўрсатиш харажатларини камайтириш бўйича режалар	1
18	2	https://t.me/c/2550852551/545	3. Таъсир қилувчи шахслар ўзимизда I Марказдаги ер нархи ўсиши тезлашган	2
19	2	https://t.me/c/2550852551/546	4. Centris Towers - қўшимча қулайликлари	3
20	2	https://t.me/c/2550852551/547	5. Бино қачон кўринади	4
21	2	https://t.me/c/2550852551/548	6. Парковка сотилмайди	5
22	2	https://t.me/c/2550852551/549	7. Centris Towers — Муваффақият Маркази	6
23	2	https://t.me/c/2550852551/550	8. Охирги пулига олинмаган	7
24	2	https://t.me/c/2550852551/551	9. Инвестиция хавфсизлиги	8
25	2	https://t.me/c/2550852551/552	10. Қурилиш битишига таъсир қилувчи омиллар	9
26	2	https://t.me/c/2550852551/553	11. Манга қўшниларим муҳим	10
27	2	https://t.me/c/2550852551/554	12. Бизга қайси сегмент қизиқ	11
28	2	https://t.me/c/2550852551/555	13. Centris Towers ғояси	12
29	2	https://t.me/c/2550852551/556	14. Centris Towers қулайликлари ва инвестиция бўйича хавфсизлиги	13
30	2	https://t.me/c/2550852551/557	15. Centris Towers — Муваффақият Маркази (Full)	14
31	3	https://t.me/c/2550852551/543	lyuboy	0
32	4	1	/start	0
33	5	https://t.me/c/2550852551/543	1. Centris Towers’даги лобби	0
34	5	https://t.me/c/2550852551/544	2. Хизмат кўрсатиш харажатларини камайтириш бўйича режалар	1
35	5	https://t.me/c/2550852551/545	3. Таъсир қилувчи шахслар ўзимизда I Марказдаги ер нархи ўсиши тезлашган	2
36	5	https://t.me/c/2550852551/546	4. Centris Towers - қўшимча қулайликлари	3
37	5	https://t.me/c/2550852551/547	5. Бино қачон кўринади	4
38	5	https://t.me/c/2550852551/548	6. Парковка сотилмайди	5
39	5	https://t.me/c/2550852551/549	7. Centris Towers — Муваффақият Маркази	6
40	5	https://t.me/c/2550852551/550	8. Охирги пулига олинмаган	7
41	5	https://t.me/c/2550852551/551	9. Инвестиция хавфсизлиги	8
42	5	https://t.me/c/2550852551/552	10. Қурилиш битишига таъсир қилувчи омиллар	9
43	5	https://t.me/c/2550852551/553	11. Манга қўшниларим муҳим	10
44	5	https://t.me/c/2550852551/554	12. Бизга қайси сегмент қизиқ	11
45	5	https://t.me/c/2550852551/555	13. Centris Towers ғояси	12
46	5	https://t.me/c/2550852551/556	14. Centris Towers қулайликлари ва инвестиция бўйича хавфсизлиги	13
47	5	https://t.me/c/2550852551/557	15. Centris Towers — Муваффақият Маркази (Full)	14
48	6	https://t.me/c/2550852551/543	1. Centris Towers’даги лобби	0
49	6	https://t.me/c/2550852551/544	2. Хизмат кўрсатиш харажатларини камайтириш бўйича режалар	1
50	6	https://t.me/c/2550852551/545	3. Таъсир қилувчи шахслар ўзимизда I Марказдаги ер нархи ўсиши тезлашган	2
51	6	https://t.me/c/2550852551/546	4. Centris Towers - қўшимча қулайликлари	3
52	6	https://t.me/c/2550852551/547	5. Бино қачон кўринади	4
53	6	https://t.me/c/2550852551/548	6. Парковка сотилмайди	5
54	6	https://t.me/c/2550852551/549	7. Centris Towers — Муваффақият Маркази	6
55	6	https://t.me/c/2550852551/550	8. Охирги пулига олинмаган	7
56	6	https://t.me/c/2550852551/551	9. Инвестиция хавфсизлиги	8
57	6	https://t.me/c/2550852551/552	10. Қурилиш битишига таъсир қилувчи омиллар	9
58	6	https://t.me/c/2550852551/553	11. Манга қўшниларим муҳим	10
59	6	https://t.me/c/2550852551/554	12. Бизга қайси сегмент қизиқ	11
60	6	https://t.me/c/2550852551/555	13. Centris Towers ғояси	12
61	6	https://t.me/c/2550852551/556	14. Centris Towers қулайликлари ва инвестиция бўйича хавфсизлиги	13
62	6	https://t.me/c/2550852551/557	15. Centris Towers — Муваффақият Маркази (Full)	14
63	7	https://t.me/c/2550852551/668	Олтинкўл лойиҳасининг бошланиш тарихи	0
64	7	https://t.me/c/2550852551/669	Лойиҳанинг энг кучли тарафи	1
65	7	https://t.me/c/2550852551/670	Лойиҳанинг муҳим жиҳатлари	2
66	7	https://t.me/c/2550852551/671	Олтинкўлнинг ҳудудий тузулиши	3
67	7	https://t.me/c/2550852551/672	Хавфсизлик қанчалик таъминланган?	4
68	7	https://t.me/c/2550852551/673	Ижтимоий жиҳатдан ёш болалилар учун қулайликлар	5
69	7	https://t.me/c/2550852551/674	Ҳудуддан чиқмасдан дўконлардан фойдаланиш	6
70	7	https://t.me/c/2550852551/675	Баландлиги ҳовлиникидай бўлган хонадонлар.	7
71	7	https://t.me/c/2550852551/676	Қадриятларга мос услубда қурилган турар жой	8
72	7	https://t.me/c/2550852551/677	Кўнгил очар манзиллар	9
73	7	https://t.me/c/2550852551/678	Парковка билан муаммосиз ҳудуд	10
74	7	https://t.me/c/2550852551/679	Экологик муаммоларга ечим	11
75	7	https://t.me/c/2550852551/680	Энг кўп эътибор ва вақтимизни олган омил	12
76	7	https://t.me/c/2550852551/681	Нечта блок ва нечта бинодан иборат?	13
77	7	https://t.me/c/2550852551/682	Инвестор фақат пулни ўйлайди!	14
78	7	https://t.me/c/2550852551/683	Лойиҳа қачон битади?	15
79	7	https://t.me/c/2550852551/684	Лойиҳа мақсади ва нархи	16
80	7	https://t.me/c/2550852551/685	Иситиш тизими қандай?	17
81	7	https://t.me/c/2550852551/686	Домнинг конкуренти бу машина!	18
82	7	https://t.me/c/2550852551/687	Тўлиқ кўрсатув	19
83	8	https://t.me/c/2550852551/543	1. Centris Towers’даги лобби	0
84	8	https://t.me/c/2550852551/544	2. Хизмат кўрсатиш харажатларини камайтириш бўйича режалар	1
85	8	https://t.me/c/2550852551/545	3. Таъсир қилувчи шахслар ўзимизда I Марказдаги ер нархи ўсиши тезлашган	2
86	8	https://t.me/c/2550852551/546	4. Centris Towers - қўшимча қулайликлари	3
87	8	https://t.me/c/2550852551/547	5. Бино қачон кўринади	4
88	8	https://t.me/c/2550852551/548	6. Парковка сотилмайди	5
89	8	https://t.me/c/2550852551/549	7. Centris Towers — Муваффақият Маркази	6
90	8	https://t.me/c/2550852551/550	8. Охирги пулига олинмаган	7
91	8	https://t.me/c/2550852551/551	9. Инвестиция хавфсизлиги	8
92	8	https://t.me/c/2550852551/552	10. Қурилиш битишига таъсир қилувчи омиллар	9
93	8	https://t.me/c/2550852551/553	11. Манга қўшниларим муҳим	10
94	8	https://t.me/c/2550852551/554	12. Бизга қайси сегмент қизиқ	11
95	8	https://t.me/c/2550852551/555	13. Centris Towers ғояси	12
96	8	https://t.me/c/2550852551/556	14. Centris Towers қулайликлари ва инвестиция бўйича хавфсизлиги	13
97	8	https://t.me/c/2550852551/557	15. Centris Towers — Муваффақият Маркази (Full)	14
98	9	1. Centris Towers’даги лобби	1. Centris Towers’даги лобби	0
99	9	2. Хизмат кўрсатиш харажатларини камайтириш бўйича режалар	2. Хизмат кўрсатиш харажатларини камайтириш бўйича режалар	1
100	9	3. Таъсир қилувчи шахслар ўзимизда I Марказдаги ер нархи ўсиши тезлашган	3. Таъсир қилувчи шахслар ўзимизда I Марказдаги ер нархи ўсиши тезлашган	2
101	9	4. Centris Towers - қўшимча қулайликлари	4. Centris Towers - қўшимча қулайликлари	3
102	9	5. Бино қачон кўринади	5. Бино қачон кўринади	4
103	9	6. Парковка сотилмайди	6. Парковка сотилмайди	5
104	9	7. Centris Towers — Муваффақият Маркази	7. Centris Towers — Муваффақият Маркази	6
105	9	8. Охирги пулига олинмаган	8. Охирги пулига олинмаган	7
106	9	9. Инвестиция хавфсизлиги	9. Инвестиция хавфсизлиги	8
107	9	10. Қурилиш битишига таъсир қилувчи омиллар	10. Қурилиш битишига таъсир қилувчи омиллар	9
108	9	11. Манга қўшниларим муҳим	11. Манга қўшниларим муҳим	10
109	9	12. Бизга қайси сегмент қизиқ	12. Бизга қайси сегмент қизиқ	11
110	9	13. Centris Towers ғояси	13. Centris Towers ғояси	12
111	9	14. Centris Towers қулайликлари ва инвестиция бўйича хавфсизлиги	14. Centris Towers қулайликлари ва инвестиция бўйича хавфсизлиги	13
112	9	15. Centris Towers — Муваффақият Маркази (Full)	15. Centris Towers — Муваффақият Маркази (Full)	14
\.


--
-- Name: group_whitelist_id_seq; Type: SEQUENCE SET; Schema: public; Owner: centris
--

SELECT pg_catalog.setval('public.group_whitelist_id_seq', 21, true);


--
-- Name: seasons_id_seq; Type: SEQUENCE SET; Schema: public; Owner: centris
--

SELECT pg_catalog.setval('public.seasons_id_seq', 9, true);


--
-- Name: support_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.support_id_seq', 1, false);


--
-- Name: user_security_id_seq; Type: SEQUENCE SET; Schema: public; Owner: centris
--

SELECT pg_catalog.setval('public.user_security_id_seq', 6, true);


--
-- Name: videos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: centris
--

SELECT pg_catalog.setval('public.videos_id_seq', 112, true);


--
-- Name: admins admins_pkey; Type: CONSTRAINT; Schema: public; Owner: centris
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_pkey PRIMARY KEY (user_id);


--
-- Name: db_version db_version_pkey; Type: CONSTRAINT; Schema: public; Owner: centris
--

ALTER TABLE ONLY public.db_version
    ADD CONSTRAINT db_version_pkey PRIMARY KEY (version);


--
-- Name: group_video_settings group_video_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: centris
--

ALTER TABLE ONLY public.group_video_settings
    ADD CONSTRAINT group_video_settings_pkey PRIMARY KEY (chat_id);


--
-- Name: group_whitelist group_whitelist_chat_id_key; Type: CONSTRAINT; Schema: public; Owner: centris
--

ALTER TABLE ONLY public.group_whitelist
    ADD CONSTRAINT group_whitelist_chat_id_key UNIQUE (chat_id);


--
-- Name: group_whitelist group_whitelist_pkey; Type: CONSTRAINT; Schema: public; Owner: centris
--

ALTER TABLE ONLY public.group_whitelist
    ADD CONSTRAINT group_whitelist_pkey PRIMARY KEY (id);


--
-- Name: seasons seasons_pkey1; Type: CONSTRAINT; Schema: public; Owner: centris
--

ALTER TABLE ONLY public.seasons
    ADD CONSTRAINT seasons_pkey1 PRIMARY KEY (id);


--
-- Name: settings settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_pkey PRIMARY KEY (key);


--
-- Name: support support_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.support
    ADD CONSTRAINT support_pkey PRIMARY KEY (id);


--
-- Name: user_security user_security_pkey; Type: CONSTRAINT; Schema: public; Owner: centris
--

ALTER TABLE ONLY public.user_security
    ADD CONSTRAINT user_security_pkey PRIMARY KEY (id);


--
-- Name: user_security user_security_user_id_key; Type: CONSTRAINT; Schema: public; Owner: centris
--

ALTER TABLE ONLY public.user_security
    ADD CONSTRAINT user_security_user_id_key UNIQUE (user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: centris
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: videos videos_pkey; Type: CONSTRAINT; Schema: public; Owner: centris
--

ALTER TABLE ONLY public.videos
    ADD CONSTRAINT videos_pkey PRIMARY KEY (id);


--
-- Name: videos videos_season_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: centris
--

ALTER TABLE ONLY public.videos
    ADD CONSTRAINT videos_season_id_fkey FOREIGN KEY (season_id) REFERENCES public.seasons(id) ON DELETE CASCADE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: centris
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


--
-- PostgreSQL database dump complete
--

