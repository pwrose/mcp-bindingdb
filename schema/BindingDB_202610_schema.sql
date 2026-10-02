-- Schema extracted from BDB-mySQL_All_202610.dmp (no data).
-- Source: https://www.bindingdb.org/rwd/bind/BDB-mySQL_All_202610_dmp.zip

-- Run in an empty MySQL 8.4 database.
SET @bindingdb_previous_foreign_key_checks = @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE `art_aut` (
  `firstname` varchar(200) DEFAULT NULL,
  `contact` varchar(3) DEFAULT NULL,
  `articleid` int NOT NULL,
  `auth_seq` int DEFAULT NULL,
  `authorid` int NOT NULL,
  `lastname` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`articleid`,`authorid`),
  CONSTRAINT `art_aut_ibfk_1` FOREIGN KEY (`articleid`) REFERENCES `article` (`articleid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `article` (
  `volume` smallint DEFAULT NULL,
  `month` char(3) DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `firstpage` int DEFAULT NULL,
  `journalid` int DEFAULT NULL,
  `articleid` int NOT NULL,
  `lastpage` int DEFAULT NULL,
  `abstract` varchar(4000) DEFAULT NULL,
  `title` varchar(300) DEFAULT NULL,
  `pmid` varchar(200) DEFAULT NULL,
  `day` char(2) DEFAULT NULL,
  `doi` varchar(60) DEFAULT NULL,
  PRIMARY KEY (`articleid`),
  KEY `journalid` (`journalid`),
  CONSTRAINT `article_ibfk_1` FOREIGN KEY (`journalid`) REFERENCES `journal` (`journalid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `article_kword` (
  `articleid` int NOT NULL,
  `kword` varchar(200) NOT NULL,
  PRIMARY KEY (`articleid`,`kword`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `assay` (
  `assayid` int NOT NULL,
  `description` varchar(4000) DEFAULT NULL,
  `assay_name` varchar(200) DEFAULT NULL,
  `entryid` int NOT NULL,
  PRIMARY KEY (`entryid`,`assayid`),
  CONSTRAINT `assay_ibfk_1` FOREIGN KEY (`entryid`) REFERENCES `entry` (`entryid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `cobweb_bdb` (
  `target_name` varchar(250) NOT NULL,
  `inhibitor_name` varchar(250) NOT NULL,
  `monomer_id` int NOT NULL,
  `affinity_type` varchar(4) NOT NULL,
  `affinity_value` float(15,4) NOT NULL,
  `affinity_value_display` varchar(20) NOT NULL,
  `affinity_strength` int NOT NULL,
  `reactant_set_id` int NOT NULL,
  `source_organism` varchar(200) NOT NULL,
  PRIMARY KEY (`target_name`,`monomer_id`,`source_organism`,`affinity_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `complex` (
  `n_pdb_ids` int DEFAULT NULL,
  `comments` varchar(2000) DEFAULT NULL,
  `pdb_ids` varchar(4000) DEFAULT NULL,
  `weight` varchar(200) DEFAULT NULL,
  `complexid` int NOT NULL,
  `component_count` int DEFAULT NULL,
  `type` varchar(200) DEFAULT NULL,
  `display_name` varchar(200) DEFAULT NULL,
  `chembl_id` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`complexid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `complex_component` (
  `componentid` int NOT NULL,
  `polymerid` int DEFAULT NULL,
  `complexid` int NOT NULL,
  `type` varchar(200) DEFAULT NULL,
  `monomerid` int DEFAULT NULL,
  PRIMARY KEY (`complexid`,`componentid`),
  CONSTRAINT `component_chk` CHECK (((`monomerid` > 0) or (`polymerid` > 0)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `complex_name` (
  `name` varchar(200) NOT NULL,
  `complexid` int NOT NULL,
  PRIMARY KEY (`complexid`,`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `data_fit_meth` (
  `data_fit_software` varchar(200) DEFAULT NULL,
  `comments` varchar(1000) DEFAULT NULL,
  `data_fit_meth_desc` varchar(200) DEFAULT NULL,
  `data_fit_meth_id` int NOT NULL,
  `software_version` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`data_fit_meth_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `entry` (
  `depoid` varchar(100) DEFAULT NULL,
  `comments` varchar(1000) DEFAULT NULL,
  `entrydate` datetime DEFAULT NULL,
  `entrytitle` varchar(300) NOT NULL,
  `entrantid` int DEFAULT NULL,
  `revised` varchar(1000) DEFAULT NULL,
  `entryid` int NOT NULL,
  `meas_tech` varchar(200) NOT NULL,
  `hold` varchar(20) DEFAULT NULL,
  `ezid` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`entryid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `entry_citation` (
  `art_purp` varchar(200) NOT NULL,
  `articleid` int NOT NULL,
  `entryid` int NOT NULL,
  PRIMARY KEY (`articleid`,`entryid`,`art_purp`),
  KEY `entryid` (`entryid`),
  CONSTRAINT `entry_citation_ibfk_1` FOREIGN KEY (`entryid`) REFERENCES `entry` (`entryid`),
  CONSTRAINT `entry_citation_ibfk_2` FOREIGN KEY (`articleid`) REFERENCES `article` (`articleid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `entry_kword` (
  `entryid` int NOT NULL,
  `kword` varchar(200) NOT NULL,
  PRIMARY KEY (`entryid`,`kword`),
  CONSTRAINT `entry_kword_ibfk_1` FOREIGN KEY (`entryid`) REFERENCES `entry` (`entryid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `enzyme_reactant_set` (
  `enzyme` varchar(200) DEFAULT NULL,
  `comments` varchar(1000) DEFAULT NULL,
  `sources` tinyint DEFAULT NULL,
  `reactant_set_id` int NOT NULL,
  `inhibitor_complexid` int DEFAULT NULL,
  `inhibitor_polymerid` int DEFAULT NULL,
  `entryid` int NOT NULL,
  `e_prep` varchar(1000) DEFAULT NULL,
  `enzyme_monomerid` int DEFAULT NULL,
  `substrate_monomerid` int DEFAULT NULL,
  `inhibitor` varchar(250) DEFAULT NULL,
  `s_prep` varchar(1000) DEFAULT NULL,
  `inhibitor_monomerid` int DEFAULT NULL,
  `enzyme_complexid` int DEFAULT NULL,
  `substrate_complexid` int DEFAULT NULL,
  `substrate_polymerid` int DEFAULT NULL,
  `enzyme_polymerid` int DEFAULT NULL,
  `category` varchar(200) DEFAULT NULL,
  `substrate` varchar(200) DEFAULT NULL,
  `i_prep` varchar(1000) DEFAULT NULL,
  PRIMARY KEY (`reactant_set_id`),
  KEY `entryid` (`entryid`),
  KEY `inhibitor_monomerid` (`inhibitor_monomerid`),
  KEY `enzyme_polymerid` (`enzyme_polymerid`),
  KEY `enzyme_complexid` (`enzyme_complexid`),
  KEY `enzyme_monomerid` (`enzyme_monomerid`),
  KEY `substrate_monomerid` (`substrate_monomerid`),
  KEY `substrate_polymerid` (`substrate_polymerid`),
  CONSTRAINT `enzyme_reactant_set_ibfk_1` FOREIGN KEY (`entryid`) REFERENCES `entry` (`entryid`),
  CONSTRAINT `enzyme_reactant_set_ibfk_2` FOREIGN KEY (`inhibitor_monomerid`) REFERENCES `monomer` (`monomerid`),
  CONSTRAINT `enzyme_reactant_set_ibfk_3` FOREIGN KEY (`enzyme_polymerid`) REFERENCES `polymer` (`polymerid`),
  CONSTRAINT `enzyme_reactant_set_ibfk_4` FOREIGN KEY (`enzyme_complexid`) REFERENCES `complex` (`complexid`),
  CONSTRAINT `enzyme_reactant_set_ibfk_5` FOREIGN KEY (`enzyme_monomerid`) REFERENCES `monomer` (`monomerid`),
  CONSTRAINT `enzyme_reactant_set_ibfk_6` FOREIGN KEY (`substrate_monomerid`) REFERENCES `monomer` (`monomerid`),
  CONSTRAINT `enzyme_reactant_set_ibfk_7` FOREIGN KEY (`substrate_polymerid`) REFERENCES `polymer` (`polymerid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `instrument` (
  `comments` varchar(1000) DEFAULT NULL,
  `manufact` varchar(200) DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `instrumentid` int NOT NULL,
  `name` varchar(200) DEFAULT NULL,
  `model` varchar(200) DEFAULT NULL,
  `type` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`instrumentid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `itc_result_a_b_ab` (
  `heat_ion_corr` varchar(20) DEFAULT NULL,
  `itc_result_a_b_ab_id` int NOT NULL,
  `stoich_param` decimal(10,4) DEFAULT NULL,
  `syr_monomerid` int DEFAULT NULL,
  `syr_react` varchar(200) DEFAULT NULL,
  `delta_h0` decimal(10,4) DEFAULT NULL,
  `cell_polymerid` int DEFAULT NULL,
  `syr_complexid` int DEFAULT NULL,
  `delta_h_obs_uncert` decimal(10,4) DEFAULT NULL,
  `delta_h_obs` decimal(10,4) DEFAULT NULL,
  `data_fit_meth_id` int DEFAULT NULL,
  `ph_uncert` decimal(10,4) DEFAULT NULL,
  `press` varchar(200) DEFAULT NULL,
  `temp_uncert` decimal(10,4) DEFAULT NULL,
  `k_uncert` decimal(20,4) DEFAULT NULL,
  `num_proton` decimal(10,4) DEFAULT NULL,
  `cell_react_purity` varchar(200) DEFAULT NULL,
  `temp` decimal(10,4) DEFAULT NULL,
  `delta_s0` decimal(10,4) DEFAULT NULL,
  `comments` varchar(1000) DEFAULT NULL,
  `cell_monomerid` int DEFAULT NULL,
  `syr_react_source` varchar(200) DEFAULT NULL,
  `instrumentid` int DEFAULT NULL,
  `syr_react_prep_meth` varchar(1000) DEFAULT NULL,
  `syr_react_purity` varchar(200) DEFAULT NULL,
  `ion_str` varchar(200) DEFAULT NULL,
  `cell_complexid` int DEFAULT NULL,
  `k` decimal(20,4) DEFAULT NULL,
  `cell_react_prep_meth` varchar(1000) DEFAULT NULL,
  `stoich_free_param` varchar(3) DEFAULT NULL,
  `heat_dil_corr` varchar(20) DEFAULT NULL,
  `entryid` int NOT NULL,
  `cell_react_source` varchar(200) DEFAULT NULL,
  `delta_h0_uncert` decimal(10,4) DEFAULT NULL,
  `delta_cp` decimal(10,4) DEFAULT NULL,
  `fit_sd` decimal(10,4) DEFAULT NULL,
  `delta_g0_uncert` decimal(10,4) DEFAULT NULL,
  `ion_str_uncert` varchar(200) DEFAULT NULL,
  `delta_g0` decimal(10,4) DEFAULT NULL,
  `delta_s0_uncert` decimal(10,4) DEFAULT NULL,
  `ph` decimal(10,4) DEFAULT NULL,
  `cell_react` varchar(200) DEFAULT NULL,
  `delta_cp_uncert` decimal(10,4) DEFAULT NULL,
  `itc_solution_id` int DEFAULT NULL,
  `press_uncert` varchar(200) DEFAULT NULL,
  `syr_polymerid` int DEFAULT NULL,
  PRIMARY KEY (`entryid`,`itc_result_a_b_ab_id`),
  CONSTRAINT `itc_result_a_b_ab_ibfk_1` FOREIGN KEY (`entryid`) REFERENCES `entry` (`entryid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `itc_run_a_b_ab` (
  `syr_react_conc` decimal(10,4) DEFAULT NULL,
  `cell_react_conc` decimal(10,4) DEFAULT NULL,
  `syr_react_conc_unit` varchar(200) DEFAULT NULL,
  `comments` varchar(1000) DEFAULT NULL,
  `raw_data_file` longtext,
  `itc_result_a_b_ab_id` int NOT NULL,
  `cell_react_vol` varchar(200) DEFAULT NULL,
  `syr_inj_vol` varchar(200) DEFAULT NULL,
  `cell_react_conc_unit` varchar(200) DEFAULT NULL,
  `itc_run_a_b_ab_id` bigint NOT NULL,
  `entryid` int NOT NULL,
  PRIMARY KEY (`entryid`,`itc_result_a_b_ab_id`,`itc_run_a_b_ab_id`),
  CONSTRAINT `itc_run_a_b_ab_ibfk_1` FOREIGN KEY (`entryid`) REFERENCES `entry` (`entryid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `journal` (
  `jour_name` varchar(300) DEFAULT NULL,
  `journalid` int NOT NULL,
  PRIMARY KEY (`journalid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `ki_result` (
  `kd_uncert` varchar(10) DEFAULT NULL,
  `ic50` varchar(15) DEFAULT NULL,
  `ki_result_id` int NOT NULL,
  `koff_uncert` varchar(10) DEFAULT NULL,
  `reactant_set_id` int NOT NULL,
  `kon` varchar(15) DEFAULT NULL,
  `solution_id` int DEFAULT NULL,
  `ic_percent` decimal(10,4) DEFAULT NULL,
  `vmax_uncert` decimal(10,4) DEFAULT NULL,
  `delta_g` decimal(10,4) DEFAULT NULL,
  `k_cat` decimal(10,4) DEFAULT NULL,
  `k_cat_uncert` decimal(10,4) DEFAULT NULL,
  `ec50` varchar(15) DEFAULT NULL,
  `koff` varchar(15) DEFAULT NULL,
  `data_fit_meth_id` int DEFAULT NULL,
  `ic_percent_def` varchar(200) DEFAULT NULL,
  `kd` varchar(15) DEFAULT NULL,
  `vmax` decimal(10,4) DEFAULT NULL,
  `ph_uncert` decimal(10,4) DEFAULT NULL,
  `e_conc_range` varchar(100) DEFAULT NULL,
  `ec50_uncert` varchar(10) DEFAULT NULL,
  `press` decimal(10,4) DEFAULT NULL,
  `i_conc_range` varchar(100) DEFAULT NULL,
  `temp_uncert` decimal(10,4) DEFAULT NULL,
  `ki` varchar(15) DEFAULT NULL,
  `kon_uncert` varchar(10) DEFAULT NULL,
  `temp` decimal(10,4) DEFAULT NULL,
  `km` decimal(20,4) DEFAULT NULL,
  `comments` varchar(1000) DEFAULT NULL,
  `instrumentid` int DEFAULT NULL,
  `assayid` int DEFAULT NULL,
  `ic50_uncert` varchar(10) DEFAULT NULL,
  `biological_data` varchar(200) DEFAULT NULL,
  `entryid` int NOT NULL,
  `delta_g_uncert` decimal(10,4) DEFAULT NULL,
  `s_conc_range` varchar(100) DEFAULT NULL,
  `km_uncert` decimal(20,4) DEFAULT NULL,
  `ki_uncert` varchar(10) DEFAULT NULL,
  `ph` decimal(10,4) DEFAULT NULL,
  `ic_percent_uncert` decimal(10,4) DEFAULT NULL,
  `press_uncert` decimal(10,4) DEFAULT NULL,
  PRIMARY KEY (`ki_result_id`),
  KEY `reactant_set_id` (`reactant_set_id`),
  KEY `entryid` (`entryid`),
  CONSTRAINT `ki_result_ibfk_1` FOREIGN KEY (`reactant_set_id`) REFERENCES `enzyme_reactant_set` (`reactant_set_id`),
  CONSTRAINT `ki_result_ibfk_2` FOREIGN KEY (`entryid`) REFERENCES `entry` (`entryid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `mono_name` (
  `name` varchar(500) DEFAULT NULL,
  `monomerid` int DEFAULT NULL,
  KEY `monomerid` (`monomerid`),
  CONSTRAINT `mono_name_ibfk_1` FOREIGN KEY (`monomerid`) REFERENCES `monomer` (`monomerid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `monomer` (
  `n_pdb_ids_sub` int DEFAULT NULL,
  `pdb_ids_exact` text,
  `comments` varchar(1000) DEFAULT NULL,
  `emp_form` varchar(200) DEFAULT NULL,
  `het_pdb` char(7) DEFAULT NULL,
  `display_name` varchar(500) DEFAULT NULL,
  `inchi_key` varchar(27) DEFAULT NULL,
  `pdb_ids_sub` text,
  `chembl_id` varchar(20) DEFAULT NULL,
  `monomerid` int NOT NULL,
  `inchi` text,
  `weight` varchar(200) DEFAULT NULL,
  `type` varchar(200) DEFAULT NULL,
  `n_pdb_ids_exact` int DEFAULT NULL,
  `smiles_string` text,
  `rdmid` int DEFAULT NULL,
  PRIMARY KEY (`monomerid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `pdb_bdb` (
  `pdbid` char(4) NOT NULL,
  `reactant_set_id_str` text,
  `reactant_set_id_90` text,
  `itc_result_a_b_ab_id_90` varchar(4000) DEFAULT NULL,
  `monomerid_str_90` text,
  `monomerid_str` text,
  `polymerid_str` text,
  `complexid_str` varchar(4000) DEFAULT NULL,
  `itc_result_a_b_ab_id_str` varchar(4000) DEFAULT NULL,
  PRIMARY KEY (`pdbid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `person` (
  `country` varchar(200) DEFAULT NULL,
  `firstname` varchar(200) DEFAULT NULL,
  `city` varchar(200) DEFAULT NULL,
  `articleid` int DEFAULT NULL,
  `middlename` varchar(200) DEFAULT NULL,
  `tel_num` varchar(200) DEFAULT NULL,
  `authorid` int DEFAULT NULL,
  `fax_num` varchar(200) DEFAULT NULL,
  `lastname` varchar(200) DEFAULT NULL,
  `institution` varchar(500) DEFAULT NULL,
  `street` varchar(200) DEFAULT NULL,
  `postalcode` varchar(200) DEFAULT NULL,
  `personid` int NOT NULL,
  `state` varchar(200) DEFAULT NULL,
  `department` varchar(500) DEFAULT NULL,
  `email` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`personid`),
  KEY `articleid` (`articleid`),
  CONSTRAINT `person_ibfk_1` FOREIGN KEY (`articleid`) REFERENCES `article` (`articleid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `phbuffer` (
  `comments` varchar(1000) DEFAULT NULL,
  `phbufferid` int NOT NULL,
  `name` varchar(200) DEFAULT NULL,
  `heat_ion_buff` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`phbufferid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `phbuffer_conc` (
  `phbufferid` int NOT NULL,
  `phbuffer_conc` varchar(200) DEFAULT NULL,
  `solution_id` int NOT NULL,
  `entryid` int NOT NULL,
  PRIMARY KEY (`entryid`,`solution_id`,`phbufferid`),
  CONSTRAINT `phbuffer_conc_ibfk_1` FOREIGN KEY (`entryid`) REFERENCES `entry` (`entryid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `poly_name` (
  `polymerid` int DEFAULT NULL,
  `name` varchar(200) DEFAULT NULL,
  KEY `polymerid` (`polymerid`),
  CONSTRAINT `poly_name_ibfk_1` FOREIGN KEY (`polymerid`) REFERENCES `polymer` (`polymerid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `polymer` (
  `component_id` bigint DEFAULT NULL,
  `comments` varchar(1000) DEFAULT NULL,
  `topology` varchar(200) DEFAULT NULL,
  `weight` varchar(200) DEFAULT NULL,
  `source_organism` varchar(200) DEFAULT NULL,
  `unpid2` varchar(300) DEFAULT NULL,
  `scientific_name` varchar(200) DEFAULT NULL,
  `type` varchar(200) DEFAULT NULL,
  `display_name` varchar(200) DEFAULT NULL,
  `res_count` int DEFAULT NULL,
  `sequence` text,
  `n_pdb_ids` int DEFAULT NULL,
  `taxid` varchar(200) DEFAULT NULL,
  `unpid1` varchar(300) DEFAULT NULL,
  `polymerid` int NOT NULL,
  `pdb_ids` varchar(4000) DEFAULT NULL,
  `short_name` varchar(20) DEFAULT NULL,
  `common_name` varchar(200) DEFAULT NULL,
  `chembl_id` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`polymerid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `regusers` (
  `zip` varchar(10) DEFAULT NULL,
  `country` varchar(5) NOT NULL,
  `firstname` varchar(20) NOT NULL,
  `city` varchar(100) DEFAULT NULL,
  `last_login` datetime DEFAULT NULL,
  `phonenumber` varchar(25) DEFAULT NULL,
  `jobposition` varchar(5) NOT NULL,
  `lastname` varchar(100) NOT NULL,
  `password` varchar(15) NOT NULL,
  `accesstimes` int DEFAULT NULL,
  `employer` varchar(100) NOT NULL,
  `userip` varchar(15) DEFAULT NULL,
  `setup` datetime DEFAULT NULL,
  `street1` varchar(100) DEFAULT NULL,
  `street2` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `email` varchar(50) NOT NULL,
  PRIMARY KEY (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `solute` (
  `comments` varchar(1000) DEFAULT NULL,
  `purpose` varchar(200) DEFAULT NULL,
  `purity` varchar(200) DEFAULT NULL,
  `name` varchar(200) DEFAULT NULL,
  `source` varchar(200) DEFAULT NULL,
  `soluteid` int NOT NULL,
  `pur_meth` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`soluteid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `solute_conc` (
  `soluteid` int NOT NULL,
  `solution_id` int NOT NULL,
  `entryid` int NOT NULL,
  `conc` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`entryid`,`solution_id`,`soluteid`),
  CONSTRAINT `solute_conc_ibfk_1` FOREIGN KEY (`entryid`) REFERENCES `entry` (`entryid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `solution_prep` (
  `comments` varchar(1000) DEFAULT NULL,
  `ph_prep` varchar(200) DEFAULT NULL,
  `temp_prep` varchar(200) DEFAULT NULL,
  `type` varchar(200) DEFAULT NULL,
  `solution_id` int NOT NULL,
  `entryid` int NOT NULL,
  PRIMARY KEY (`entryid`,`solution_id`),
  CONSTRAINT `solution_prep_ibfk_1` FOREIGN KEY (`entryid`) REFERENCES `entry` (`entryid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `solvent` (
  `solventid` int NOT NULL,
  `comments` varchar(1000) DEFAULT NULL,
  `purity` varchar(200) DEFAULT NULL,
  `name` varchar(200) DEFAULT NULL,
  `source` varchar(200) DEFAULT NULL,
  `pur_meth` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`solventid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `solvent_fract` (
  `solventid` int NOT NULL,
  `conc_or_fract` varchar(200) DEFAULT NULL,
  `solution_id` int NOT NULL,
  `entryid` int NOT NULL,
  PRIMARY KEY (`entryid`,`solution_id`,`solventid`),
  CONSTRAINT `solvent_fract_ibfk_1` FOREIGN KEY (`entryid`) REFERENCES `entry` (`entryid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS = @bindingdb_previous_foreign_key_checks;
