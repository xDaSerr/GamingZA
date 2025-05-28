-- 1. Crear la base de datos
CREATE SCHEMA IF NOT EXISTS serrano583;
USE serrano583;

-- 2. Crear tabla habitacion
CREATE TABLE habitacion (
    noHab INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(10),
    ubicacion VARCHAR(20),
    ocupada TINYINT DEFAULT FALSE,
    descripcion VARCHAR(45),
    costo FLOAT
);

-- 3. Crear tabla reservacion
CREATE TABLE reservacion (
    noRes INT AUTO_INCREMENT PRIMARY KEY,
    huesped VARCHAR(45),
    fechaR DATE,
    fechaE DATE,
    fechaS DATE,
    tipoH VARCHAR(10),
    noHabitacion INT DEFAULT NULL,
    pago FLOAT DEFAULT 0,
    liberada TINYINT DEFAULT FALSE
);

-- 4. Insertar habitaciones de prueba
INSERT INTO habitacion (tipo, ubicacion, descripcion, costo)
VALUES 
('sencilla', 'piso 1', 'Hab sencilla', 500),
('doble', 'piso 2', 'Hab doble', 800),
('suite', 'piso 3', 'Suite con vista', 1500);

-- 1. Hacer un procedimiento para insertar una nueva reservación, debe recibir los mininos parámetros necesarios.
DELIMITER //
CREATE PROCEDURE reservacion (
    IN p_huesped VARCHAR(45),
    IN p_fechaR DATE,
    IN p_fechaS DATE,
    IN p_tipoH VARCHAR(10)
)
BEGIN
    INSERT INTO reservacion (huesped, fechaR, fechaE, fechaS, tipoH)
    VALUES (p_huesped, p_fechaR, p_fechaR, p_fechaS, p_tipoH);
END;
//
DELIMITER ;

-- 2. Crea una función que le llegue un tipo de habitación y regrese la primera habitación disponible de ese tipo.
DELIMITER //
CREATE FUNCTION obtenerHabDisponible(p_tipo VARCHAR(10))
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE v_noHab INT;
    SELECT noHab INTO v_noHab
    FROM habitacion
    WHERE tipo = p_tipo AND ocupada = 0
    LIMIT 1;
    RETURN v_noHab;
END;
//
DELIMITER ;

-- 3. Crea procedimiento almacenado para realizar el CHECK IN de la reservación debe de recibir el nombre del huésped y actualizar noHabitacion por la habitación disponible de ese tipo.
DELIMITER //
CREATE PROCEDURE checkIN(p_huesped VARCHAR(45))
BEGIN
    DECLARE v_tipoH VARCHAR(10);
    DECLARE v_noRes INT;
    DECLARE v_noHab INT;

    SELECT tipoH, noRes INTO v_tipoH, v_noRes
    FROM reservacion
    WHERE huesped = p_huesped AND noHabitacion IS NULL AND liberada = 0
    LIMIT 1;

    SET v_noHab = obtenerHabDisponible(v_tipoH);

    IF v_noHab IS NOT NULL THEN
        UPDATE reservacion
        SET noHabitacion = v_noHab
        WHERE noRes = v_noRes;

        UPDATE habitacion
        SET ocupada = 1
        WHERE noHab = v_noHab;
    END IF;
END;
//
DELIMITER ;

-- 4. Crea procedimiento almacenado para realizar el CHECK OUT de la reservación debe de recibir el número de habitación, actualizar liberada a true y calcular su pago
DELIMITER //
CREATE PROCEDURE checkOUT(p_noHab INT)
BEGIN
    DECLARE v_noRes INT;
    DECLARE v_fechaE DATE;
    DECLARE v_fechaS DATE;
    DECLARE v_dias INT;
    DECLARE v_costo FLOAT;
    DECLARE v_total FLOAT;

    SELECT noRes, fechaE, fechaS INTO v_noRes, v_fechaE, v_fechaS
    FROM reservacion
    WHERE noHabitacion = p_noHab AND liberada = 0
    LIMIT 1;

    SET v_dias = DATEDIFF(v_fechaS, v_fechaE);

    SELECT costo INTO v_costo
    FROM habitacion
    WHERE noHab = p_noHab;

    SET v_total = v_dias * v_costo;

    UPDATE reservacion
    SET pago = v_total,
        liberada = 1
    WHERE noRes = v_noRes;

    UPDATE habitacion
    SET ocupada = 0
    WHERE noHab = p_noHab;
END;
//
DELIMITER ;

-- 5. Crea un disparador que cuando se realice un CHECK IN de reservación, actualice la tabla habitación, ocupada a true.
DELIMITER //
CREATE TRIGGER trg_checkin_ocupar_habitacion
AFTER UPDATE ON reservacion
FOR EACH ROW
BEGIN
    IF OLD.noHabitacion IS NULL AND NEW.noHabitacion IS NOT NULL THEN
        UPDATE habitacion
        SET ocupada = 1
        WHERE noHab = NEW.noHabitacion;
    END IF;
END;
//
DELIMITER ;

-- 6. Crea un disparador que cuando el huésped realice un CHECK OUT, actualice la tabla habitación, ocupada a false.
DELIMITER //
CREATE TRIGGER trg_checkout_liberar_habitacion
AFTER UPDATE ON reservacion
FOR EACH ROW
BEGIN
    IF OLD.liberada = 0 AND NEW.liberada = 1 THEN
        UPDATE habitacion
        SET ocupada = 0
        WHERE noHab = NEW.noHabitacion;
    END IF;
END;
//
DELIMITER ;

-- Insertar reservaciones para pruebas
CALL reservacion('Luis', '2025-06-01', '2025-06-05', 'sencilla');
CALL reservacion('Ana',  '2025-06-01', '2025-06-03', 'doble');
CALL reservacion('Paco', '2025-06-01', '2025-06-06', 'suite');

-- Probar CHECK IN y CHECK OUT
CALL checkIN('Luis');
CALL checkOUT(1);

-- Consultar resultados
SELECT * FROM habitacion;
SELECT * FROM reservacion;
