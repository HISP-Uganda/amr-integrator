CREATE TABLE facilities(
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(64) NOT NULL DEFAULT '', -- as in DISIS
    dhis2_name VARCHAR(64) NOT NULL,
    dhis2id VARCHAR(64) NOT NULL DEFAULT '',
    created TIMESTAMP DEFAULT NOW(),
    updated TIMESTAMP DEFAULT NOW()
);

CREATE TABLE organisms (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    code VARCHAR(3),
    in_dhis2 BOOLEAN NOT NULL DEFAULT FALSE,
    dhis2_order INT,
    created TIMESTAMP DEFAULT NOW(),
    updated TIMESTAMP DEFAULT NOW()
);

CREATE TABLE antibiotics (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    code VARCHAR(3),
    disis_code VARCHAR(16),
    in_dhis2 BOOLEAN NOT NULL DEFAULT FALSE,
    dhis2_order INT,
    created TIMESTAMP DEFAULT NOW(),
    updated TIMESTAMP DEFAULT NOW()
);
-- amx_salmonella_spp_resistant
-- code_organism_resistant, code_organism_susceptible, code_organism_intermediate
CREATE TABLE indicator_mapping(
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    form VARCHAR(32) NOT NULL,
    slug VARCHAR(32) NOT NULL,
    cmd VARCHAR(32) NOT NULL,
    form_order INT,
    description VARCHAR(128) NOT NULL DEFAULT '',
    dataset VARCHAR(11) NOT NULL,
    dataelement VARCHAR(11) NOT NULL,
    category_option_combo VARCHAR(11) NOT NULL,
    created TIMESTAMP DEFAULT NOW(),
    updated TIMESTAMP DEFAULT NOW()
);
