CREATE DATABASE IF NOT EXISTS DB_FIREZONE;
USE DB_FIREZONE;

CREATE TABLE admin_member(
   am_no         INT         AUTO_INCREMENT      COMMENT '관리자 회원번호',
   am_id         VARCHAR(20)   NOT NULL   UNIQUE   COMMENT '관리자 아이디',
   am_pw         VARCHAR(100) NOT NULL         COMMENT '관리자 비밀번호',
   am_name      VARCHAR(20)   NOT NULL          COMMENT '관리자 이름',
   am_phone      VARCHAR(20)   NOT NULL         COMMENT   '관리자 연락처',
   am_mail      VARCHAR(30) NOT NULL             COMMENT '관리자 메일',
   am_authority_no INT DEFAULT 1 COMMENT '관리자 권한번호',
   am_reg_date   TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
   am_mod_date   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
   
   PRIMARY KEY(am_no)
);

SELECT * FROM admin_member;
DESC admin_member;

CREATE TABLE user_member(
   um_no         INT         AUTO_INCREMENT      COMMENT '회원 회원번호',
   um_id         VARCHAR(20)   NOT NULL   UNIQUE   COMMENT '회원 아이디',
   um_pw         VARCHAR(100) NOT NULL         COMMENT '회원 비밀번호',
   um_name      VARCHAR(20)   NOT NULL          COMMENT '회원 이름',
   um_phone      VARCHAR(20)   NOT NULL         COMMENT   '회원 연락처',
   um_mail      VARCHAR(30) NOT NULL             COMMENT '회원 메일',
   um_reg_date   TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
   um_mod_date   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
   
   PRIMARY KEY(um_no)
);

SELECT * FROM user_member;
DESC user_member;

CREATE TABLE admin_authority(
   aa_no          INT AUTO_INCREMENT COMMENT '관리자 권한번호',
   aa_role_name   VARCHAR(20) NOT NULL COMMENT '관리자 권한명',

   PRIMARY KEY(aa_no)
);

SELECT * FROM admin_authority;
DESC admin_authority;

CREATE TABLE admin_authority_history(
   aah_no              INT AUTO_INCREMENT COMMENT '권한 변경 이력번호',
   aah_admin_no        INT NOT NULL COMMENT '권한이 변경된 관리자 회원번호',
   aah_before_auth_no  INT COMMENT '변경 전 권한번호',
   aah_after_auth_no   INT NOT NULL COMMENT '변경 후 권한번호',
   aah_changed_by      INT NOT NULL COMMENT '권한을 변경한 관리자 회원번호',
   aah_changed_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '권한 변경일',

   PRIMARY KEY(aah_no)
);

SELECT * FROM admin_authority_history;
DESC admin_authority_history;

SELECT * FROM admin_member am
JOIN admin_authority aa
ON am.am_authority_no = aa.aa_no
ORDER BY am.am_no DESC;

CREATE TABLE detection_log(
   dl_no                 INT AUTO_INCREMENT COMMENT '탐지 기록번호',
   dl_camera_id          VARCHAR(20) NOT NULL COMMENT '감지 카메라 ID',
   dl_zone_no            VARCHAR(20) COMMENT '탐지 구역번호',
   dl_violation_type     VARCHAR(30) NOT NULL COMMENT '위반 유형',
   dl_car_number         VARCHAR(20) COMMENT '인식 차량번호',
   dl_image_path         VARCHAR(255) COMMENT '탐지 이미지 경로',
   dl_first_detected_at  TIMESTAMP COMMENT '최초 탐지 시간',
   dl_last_detected_at   TIMESTAMP COMMENT '마지막 탐지 시간',

   PRIMARY KEY(dl_no)
);

SELECT * FROM detection_log;
DESC detection_log;

SELECT * FROM detection_log
ORDER BY dl_no DESC;

CREATE TABLE system_log(
   sl_no          INT AUTO_INCREMENT COMMENT '시스템 로그번호',
   sl_action      VARCHAR(100) NOT NULL COMMENT '시스템 활동 내용',
   sl_created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '로그 발생 시간',
   PRIMARY KEY(sl_no)
);

SELECT * FROM system_log;
DESC system_log;

SELECT * FROM system_log
ORDER BY sl_no DESC;

SHOW TABLES;

CREATE TABLE user_authority(
ua_no			INT AUTO_INCREMENT		COMMENT	'유저 권한번호',
ua_role_name	VARCHAR(20)	NOT NULL	COMMENT	'유저 권한명',
PRIMARY KEY(ua_no)

);

SELECT * from user_authority;
desc user_authority;
