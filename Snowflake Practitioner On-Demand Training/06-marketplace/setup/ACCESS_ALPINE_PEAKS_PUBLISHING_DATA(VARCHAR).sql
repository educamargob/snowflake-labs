-- THIS STORE PROCEDURE SHOULD BE OWNED BY ACCOUNTADMIN OR A ROLE THAT STUDENTS CAN'T USE

-- THERE SHOULD BE A GRANT FOR THIS SP TO PUBLIC OR INDIVIDUALLY TO THE STUDENT'S ROLE

-- ADDITIONALLY, THE ALPINE_PEAKS_PUBLISHING private-share listing MUST be mounted on the account (instructor / setup) PRIOR TO TRAINING.
-- NOTE: the lab notebook calls COMMON_DB.RESOURCES.ACCESS_ALPINE_PEAKS_PUBLISHING_DATA, so the proc lives in COMMON_DB.RESOURCES (matches vbb30699 deployment).

CREATE OR REPLACE PROCEDURE COMMON_DB.RESOURCES.ACCESS_ALPINE_PEAKS_PUBLISHING_DATA("ROLE" VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS '
BEGIN
    LET sql_stmt1 := ''GRANT IMPORTED PRIVILEGES ON DATABASE alpine_peaks_publishing TO ROLE '' || role || '';'';
    EXECUTE IMMEDIATE (sql_stmt1);

    RETURN ''Success. Privileges to access ALPINE_PEAKS_PUBLISHING database granted to role: '' || upper(role);

EXCEPTION
    WHEN OTHER THEN
        RETURN OBJECT_CONSTRUCT(''Error type'', ''Other error'',
                            ''SQLCODE'', sqlcode,
                            ''SQLERRM'', sqlerrm,
                            ''SQLSTATE'', sqlstate);
    
END;
';

-- Students call this proc from their _RL role, so grant USAGE to PUBLIC (as deployed on vbb30699).
GRANT USAGE ON PROCEDURE COMMON_DB.RESOURCES.ACCESS_ALPINE_PEAKS_PUBLISHING_DATA(VARCHAR) TO ROLE PUBLIC;