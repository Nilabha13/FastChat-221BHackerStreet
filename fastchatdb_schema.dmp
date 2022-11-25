--
-- PostgreSQL database dump
--

-- Dumped from database version 15.0 (Ubuntu 15.0-1.pgdg22.04+1)
-- Dumped by pg_dump version 15.0 (Ubuntu 15.0-1.pgdg22.04+1)

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
-- Name: group_messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.group_messages (
    group_message_id integer NOT NULL,
    group_id integer,
    from_user_id integer,
    message_type text,
    filename text
);


ALTER TABLE public.group_messages OWNER TO postgres;

--
-- Name: groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.groups (
    group_name text,
    group_admin text,
    group_members text
);


ALTER TABLE public.groups OWNER TO postgres;

--
-- Name: individual_messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.individual_messages (
    from_user_name text,
    to_user_name text,
    message_content text,
    message_type text,
    filename text,
    class text,
    groupname text,
    time_sent text
);


ALTER TABLE public.individual_messages OWNER TO postgres;

--
-- Name: keyserver; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.keyserver (
    username text NOT NULL,
    public_key text,
    type text
);


ALTER TABLE public.keyserver OWNER TO postgres;

--
-- Name: messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.messages (
    from_user_name text,
    to_user_name text,
    message_content text,
    message_type text,
    filename text,
    class text,
    groupname text,
    time_sent text
);


ALTER TABLE public.messages OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    username text,
    salt text,
    password_hash text,
    current_server_number integer
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: group_messages group_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.group_messages
    ADD CONSTRAINT group_messages_pkey PRIMARY KEY (group_message_id);


--
-- Name: keyserver keyserver_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.keyserver
    ADD CONSTRAINT keyserver_pkey PRIMARY KEY (username);


--
-- PostgreSQL database dump complete
--

