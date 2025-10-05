# Sistemas_operativos_2

Reto 2 

Sistema de chat con colas System V (servidor/cliente)

Compilar:
  make

Ejecutar servidor:
  ./servidor

Abrir varios clientes (en terminales distintas):
  ./cliente Alice
  ./cliente Bob

Comandos del cliente:
  /join <sala>     -> unirse a la sala indicada
  /leave           -> (opcional) abandonar la sala
  /quit            -> salir del cliente
  <texto libre>    -> enviar texto a la sala actual

Notas:
- El cliente crea una cola privada y la comunica al servidor en el JOIN.
- El servidor reenvía mensajes a las colas privadas de los clientes en la sala (excepto al remitente).
- Para detener el servidor: CTRL+C (el servidor elimina la cola global antes de salir).
- Ajustar MAX_SALAS y MAX_USUARIOS en servidor.c si se necesita mayor capacidad.
