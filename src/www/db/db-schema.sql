-- phpMyAdmin SQL Dump
-- version 2.6.1
-- http://www.phpmyadmin.net
-- 
-- Host: localhost
-- Generation Time: Mar 10, 2005 at 09:26 PM
-- Server version: 3.23.54
-- PHP Version: 4.2.2
-- 
-- Database: `uts`
-- 

-- --------------------------------------------------------

-- 
-- Table structure for table `logged`
-- 

DROP TABLE IF EXISTS `logged`;
CREATE TABLE IF NOT EXISTS `logged` (
  `id` smallint(5) NOT NULL default '0'
) TYPE=MyISAM;

-- --------------------------------------------------------

-- 
-- Table structure for table `setup`
-- 

DROP TABLE IF EXISTS `setup`;
CREATE TABLE IF NOT EXISTS `setup` (
  `admin` varchar(40) NOT NULL default '',
  `admin_pass` varchar(40) NOT NULL default ''
) TYPE=MyISAM;

-- --------------------------------------------------------

-- 
-- Table structure for table `user_info`
-- 

DROP TABLE IF EXISTS `user_info`;
CREATE TABLE IF NOT EXISTS `user_info` (
  `user_id` smallint(5) unsigned NOT NULL default '0',
  PRIMARY KEY  (`user_id`)
) TYPE=MyISAM;

-- --------------------------------------------------------

-- 
-- Table structure for table `user_sched`
-- 

DROP TABLE IF EXISTS `user_sched`;
CREATE TABLE IF NOT EXISTS `user_sched` (
  `user_id` smallint(5) unsigned NOT NULL default '0',
  `id` int(10) unsigned NOT NULL default '0',
  `inicio` int(10) unsigned NOT NULL default '0',
  `fim` int(10) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`)
) TYPE=MyISAM;

-- --------------------------------------------------------

-- 
-- Table structure for table `users`
-- 

DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users` (
  `id` smallint(5) unsigned NOT NULL default '0',
  `nome` varchar(255) default NULL,
  `username` varchar(40) NOT NULL default '',
  `root` tinyint(1) unsigned NOT NULL default '0',
  `passwd` varchar(40) NOT NULL default '',
  PRIMARY KEY  (`id`)
) TYPE=MyISAM;
