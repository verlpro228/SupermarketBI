-- ============================================================
-- 超市库存管理日常业务数据分析及可视化系统
-- 数据库初始化脚本（MySQL 8.0）
-- 执行方式：mysql -u root -p < init_db.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS `supermarket_bi`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE `supermarket_bi`;

-- ------------------------------------------------------------
-- 1. 商品分类
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `category` (
  `id`         BIGINT   NOT NULL AUTO_INCREMENT,
  `name`       VARCHAR(50)  NOT NULL COMMENT '分类名称',
  `sort_order` SMALLINT NOT NULL DEFAULT 0 COMMENT '排序号',
  `status`     SMALLINT NOT NULL DEFAULT 1 COMMENT '1 启用 0 停用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_category_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='商品分类';

-- ------------------------------------------------------------
-- 2. 系统用户
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sys_user` (
  `id`            BIGINT NOT NULL AUTO_INCREMENT,
  `username`      VARCHAR(50)  NOT NULL COMMENT '登录账号',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
  `real_name`     VARCHAR(50)  DEFAULT NULL COMMENT '姓名',
  `role`          VARCHAR(20)  NOT NULL DEFAULT 'keeper' COMMENT 'admin 管理员 / keeper 库管员',
  `status`        SMALLINT NOT NULL DEFAULT 1 COMMENT '1 启用 0 禁用',
  `last_login_at` DATETIME DEFAULT NULL COMMENT '最后登录时间',
  `created_at`    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_username` (`username`),
  KEY `idx_user_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统用户';

-- ------------------------------------------------------------
-- 3. 商品档案
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `product` (
  `id`              BIGINT NOT NULL AUTO_INCREMENT,
  `barcode`         VARCHAR(64)  NOT NULL COMMENT '条码',
  `name`            VARCHAR(128) NOT NULL COMMENT '商品名称',
  `category_id`     BIGINT NOT NULL COMMENT '分类ID',
  `spec`            VARCHAR(64)  DEFAULT NULL COMMENT '规格',
  `unit`            VARCHAR(16)  DEFAULT NULL COMMENT '单位',
  `purchase_price`  DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '进价',
  `sale_price`      DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '售价',
  `safe_stock`      DECIMAL(12,3) NOT NULL DEFAULT 0.000 COMMENT '安全库存',
  `shelf_life_days` SMALLINT NOT NULL DEFAULT 0 COMMENT '保质期天数',
  `status`          SMALLINT NOT NULL DEFAULT 1 COMMENT '1 正常 0 已停用',
  `created_at`      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_product_barcode` (`barcode`),
  KEY `idx_product_name` (`name`),
  KEY `idx_product_category` (`category_id`),
  KEY `idx_product_status` (`status`),
  CONSTRAINT `fk_product_category` FOREIGN KEY (`category_id`) REFERENCES `category` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='商品档案';

-- ------------------------------------------------------------
-- 4. 商品库存汇总（出库原子扣减用）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `inventory` (
  `product_id` BIGINT NOT NULL COMMENT '商品ID',
  `total_qty`  DECIMAL(12,3) NOT NULL DEFAULT 0.000 COMMENT '当前库存总量',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`product_id`),
  CONSTRAINT `fk_inventory_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='商品库存汇总';

-- ------------------------------------------------------------
-- 5. 入库单
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `inbound_order` (
  `id`              BIGINT NOT NULL AUTO_INCREMENT,
  `order_no`        VARCHAR(32) NOT NULL COMMENT '入库单号',
  `product_id`      BIGINT NOT NULL COMMENT '商品ID',
  `quantity`        DECIMAL(12,3) NOT NULL COMMENT '入库数量',
  `cost_price`      DECIMAL(12,2) NOT NULL COMMENT '入库进价',
  `amount`          DECIMAL(14,2) NOT NULL COMMENT '入库金额（后端计算）',
  `production_date` DATE NOT NULL COMMENT '生产日期',
  `expiry_date`     DATE NOT NULL COMMENT '到期日',
  `supplier`        VARCHAR(128) DEFAULT NULL COMMENT '供应商',
  `operator_id`     BIGINT NOT NULL COMMENT '操作人ID',
  `remark`          VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_inbound_order_no` (`order_no`),
  KEY `idx_inbound_product` (`product_id`),
  KEY `idx_inbound_created` (`created_at`),
  KEY `idx_inbound_operator` (`operator_id`),
  CONSTRAINT `fk_inbound_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`),
  CONSTRAINT `fk_inbound_operator` FOREIGN KEY (`operator_id`) REFERENCES `sys_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='入库单';

-- ------------------------------------------------------------
-- 6. 批次库存
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `inventory_batch` (
  `id`              BIGINT NOT NULL AUTO_INCREMENT,
  `product_id`      BIGINT NOT NULL COMMENT '商品ID',
  `batch_no`        VARCHAR(32) NOT NULL COMMENT '批次号',
  `inbound_id`      BIGINT DEFAULT NULL COMMENT '来源入库单ID',
  `production_date` DATE NOT NULL COMMENT '生产日期',
  `expiry_date`     DATE NOT NULL COMMENT '到期日',
  `qty_initial`     DECIMAL(12,3) NOT NULL COMMENT '入库数量',
  `qty_remaining`   DECIMAL(12,3) NOT NULL COMMENT '剩余数量',
  `cost_price`      DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '批次进价',
  `is_promo`        SMALLINT NOT NULL DEFAULT 0 COMMENT '1 已标记促销',
  `created_at`      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_batch_no` (`batch_no`),
  KEY `idx_batch_product` (`product_id`),
  KEY `idx_batch_expiry` (`expiry_date`),
  KEY `idx_batch_inbound` (`inbound_id`),
  CONSTRAINT `fk_batch_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`),
  CONSTRAINT `fk_batch_inbound` FOREIGN KEY (`inbound_id`) REFERENCES `inbound_order` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='批次库存';

-- ------------------------------------------------------------
-- 7. 出库单
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `outbound_order` (
  `id`            BIGINT NOT NULL AUTO_INCREMENT,
  `order_no`      VARCHAR(32) NOT NULL COMMENT '出库单号',
  `outbound_type` VARCHAR(10) NOT NULL COMMENT 'sale 销售 / loss 报损',
  `total_qty`     DECIMAL(12,3) NOT NULL COMMENT '出库总数量',
  `total_amount`  DECIMAL(14,2) NOT NULL DEFAULT 0.00 COMMENT '出库总金额（后端计算）',
  `reason`        VARCHAR(255) DEFAULT NULL COMMENT '报损原因',
  `operator_id`   BIGINT NOT NULL COMMENT '操作人ID',
  `remark`        VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_outbound_order_no` (`order_no`),
  KEY `idx_outbound_type` (`outbound_type`),
  KEY `idx_outbound_created` (`created_at`),
  KEY `idx_outbound_operator` (`operator_id`),
  CONSTRAINT `fk_outbound_operator` FOREIGN KEY (`operator_id`) REFERENCES `sys_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='出库单';

-- ------------------------------------------------------------
-- 8. 出库明细（按批次拆分）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `outbound_item` (
  `id`          BIGINT NOT NULL AUTO_INCREMENT,
  `outbound_id` BIGINT NOT NULL COMMENT '出库单ID',
  `product_id`  BIGINT NOT NULL COMMENT '商品ID',
  `batch_id`    BIGINT NOT NULL COMMENT '批次ID',
  `quantity`    DECIMAL(12,3) NOT NULL COMMENT '本批次出库数量',
  `cost_price`  DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '批次进价快照',
  `amount`      DECIMAL(14,2) NOT NULL DEFAULT 0.00 COMMENT '本批次出库金额',
  PRIMARY KEY (`id`),
  KEY `idx_outitem_order` (`outbound_id`),
  KEY `idx_outitem_product` (`product_id`),
  KEY `idx_outitem_batch` (`batch_id`),
  CONSTRAINT `fk_outitem_order` FOREIGN KEY (`outbound_id`) REFERENCES `outbound_order` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_outitem_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`),
  CONSTRAINT `fk_outitem_batch` FOREIGN KEY (`batch_id`) REFERENCES `inventory_batch` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='出库明细（按批次拆分）';

-- ------------------------------------------------------------
-- 9. 库存调整日志
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `stock_adjust_log` (
  `id`          BIGINT NOT NULL AUTO_INCREMENT,
  `product_id`  BIGINT NOT NULL COMMENT '商品ID',
  `batch_id`    BIGINT NOT NULL COMMENT '调整批次ID',
  `before_qty`  DECIMAL(12,3) NOT NULL COMMENT '调整前数量',
  `after_qty`   DECIMAL(12,3) NOT NULL COMMENT '调整后数量',
  `diff_qty`    DECIMAL(12,3) NOT NULL COMMENT '差异数量',
  `reason`      VARCHAR(255) NOT NULL COMMENT '调整原因',
  `operator_id` BIGINT NOT NULL COMMENT '操作人ID',
  `created_at`  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_adjust_product` (`product_id`),
  KEY `idx_adjust_created` (`created_at`),
  KEY `idx_adjust_operator` (`operator_id`),
  CONSTRAINT `fk_adjust_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`),
  CONSTRAINT `fk_adjust_batch` FOREIGN KEY (`batch_id`) REFERENCES `inventory_batch` (`id`),
  CONSTRAINT `fk_adjust_operator` FOREIGN KEY (`operator_id`) REFERENCES `sys_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='库存调整日志';

-- ------------------------------------------------------------
-- 10. 临期处理记录
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `expiry_action_log` (
  `id`          BIGINT NOT NULL AUTO_INCREMENT,
  `product_id`  BIGINT NOT NULL COMMENT '商品ID',
  `batch_id`    BIGINT NOT NULL COMMENT '批次ID',
  `action`      VARCHAR(10) NOT NULL COMMENT 'loss 报损 / promo 标记促销',
  `quantity`    DECIMAL(12,3) NOT NULL DEFAULT 0.000 COMMENT '处理数量',
  `outbound_id` BIGINT DEFAULT NULL COMMENT '关联报损出库单ID',
  `operator_id` BIGINT NOT NULL COMMENT '处理人ID',
  `created_at`  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '处理时间',
  PRIMARY KEY (`id`),
  KEY `idx_expiry_product` (`product_id`),
  KEY `idx_expiry_batch` (`batch_id`),
  KEY `idx_expiry_created` (`created_at`),
  KEY `idx_expiry_operator` (`operator_id`),
  KEY `idx_expiry_outbound` (`outbound_id`),
  CONSTRAINT `fk_expiry_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`),
  CONSTRAINT `fk_expiry_batch` FOREIGN KEY (`batch_id`) REFERENCES `inventory_batch` (`id`),
  CONSTRAINT `fk_expiry_operator` FOREIGN KEY (`operator_id`) REFERENCES `sys_user` (`id`),
  CONSTRAINT `fk_expiry_outbound` FOREIGN KEY (`outbound_id`) REFERENCES `outbound_order` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='临期处理记录';

-- ------------------------------------------------------------
-- 11. 库存巡检记录
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `inspection_record` (
  `id`           BIGINT NOT NULL AUTO_INCREMENT,
  `inspector_id` BIGINT NOT NULL COMMENT '执行人ID',
  `hit_count`    INT NOT NULL DEFAULT 0 COMMENT '命中条数',
  `created_at`   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '巡检时间',
  PRIMARY KEY (`id`),
  KEY `idx_inspection_created` (`created_at`),
  KEY `idx_inspection_user` (`inspector_id`),
  CONSTRAINT `fk_inspection_user` FOREIGN KEY (`inspector_id`) REFERENCES `sys_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='库存巡检记录';

-- ------------------------------------------------------------
-- 12. 巡检问题明细（快照）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `inspection_item` (
  `id`           BIGINT NOT NULL AUTO_INCREMENT,
  `record_id`    BIGINT NOT NULL COMMENT '巡检记录ID',
  `product_id`   BIGINT NOT NULL COMMENT '商品ID',
  `batch_id`     BIGINT DEFAULT NULL COMMENT '批次ID（低库存为空）',
  `problem_type` VARCHAR(20) NOT NULL COMMENT 'low_stock 低库存 / near_expiry 临期',
  `gap_qty`      DECIMAL(12,3) DEFAULT NULL COMMENT '低库存缺口数量',
  `days_left`    INT DEFAULT NULL COMMENT '剩余保质期天数快照',
  `status`       VARCHAR(10) NOT NULL DEFAULT 'pending' COMMENT 'pending/handled/ignored',
  `handled_at`   DATETIME DEFAULT NULL COMMENT '处理时间',
  PRIMARY KEY (`id`),
  KEY `idx_item_record` (`record_id`),
  KEY `idx_item_product` (`product_id`),
  KEY `idx_item_batch` (`batch_id`),
  CONSTRAINT `fk_item_record` FOREIGN KEY (`record_id`) REFERENCES `inspection_record` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_item_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`),
  CONSTRAINT `fk_item_batch` FOREIGN KEY (`batch_id`) REFERENCES `inventory_batch` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='巡检问题明细（快照）';

-- ------------------------------------------------------------
-- 13. 系统配置
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sys_config` (
  `id`           BIGINT NOT NULL AUTO_INCREMENT,
  `config_key`   VARCHAR(64) NOT NULL COMMENT '配置键',
  `config_value` VARCHAR(255) NOT NULL COMMENT '配置值',
  `description`  VARCHAR(255) DEFAULT NULL COMMENT '说明',
  `updated_at`   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统配置项';

-- ------------------------------------------------------------
-- 初始配置数据
-- ------------------------------------------------------------
INSERT INTO `sys_config` (`config_key`, `config_value`, `description`) VALUES
  ('expiry_urgent_days',  '7',  '临期-紧急分档阈值（剩余天数）'),
  ('expiry_warning_days', '30', '临期-预警分档阈值（剩余天数）')
ON DUPLICATE KEY UPDATE `description` = VALUES(`description`);
