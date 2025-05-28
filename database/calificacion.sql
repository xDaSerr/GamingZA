use calificaciones;

INSERT INTO alumno
values("120731", "Valeria", "8.0");

DROP TRIGGER updatePromedio;
SHOW TRIGGERS;

DELIMITER //
CREATE TRIGGER updatePromedio
AFTER INSERT ON calificacion
FOR EACH ROW BEGIN
			-- actualizamos el promedio en la tabla alumno
		UPDATE alumno 
        SET promedio = (select avg(cal) 
						from calificacion
                        where control = new.control)
					where control = new.control;
					
END// 
DELIMITER ;

DELIMITER //
CREATE TRIGGER updateCal
AFTER INSERT ON calificacion
FOR EACH ROW BEGIN
			-- actualizamos el promedio en la tabla alumno
		UPDATE alumno 
        SET promedio = (select avg(cal) 
						from calificacion
                        where control = new.control);
			
END// 
DELIMITER ;

UPDATE calificacion
SET cal = 100.00
WHERE control = '120731' and unidad  = '1';

SELECT * FROM alumno;
SELECT * FROM calificacion;
				
