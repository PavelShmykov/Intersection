import pygame


class Vehicle(pygame.sprite.Sprite):
    def __init__(self, speed, lane, direction_number, direction, will_turn, simulation):
        """
        Конструктор транспортного средства.
        - Определяет начальные параметры движения машины, её положение и изображения.
        - Добавляет объект в соответствующую категорию (список машин, группу Pygame).
        """

        # Инициализируем объект Pygame Sprite (машина теперь является спрайтом)
        pygame.sprite.Sprite.__init__(self)

        # Сохраняем ссылку на объект симуляции (главный класс)
        self.simulation = simulation

        # Определяем основные параметры машины
        self.lane = lane  # Номер полосы
        self.speed = speed  # Скорость движения машины
        self.base_speed = self.speed  # Базовая скорость (может изменяться)
        self.vehicleClass = self.__class__.__name__.lower()  # Название класса машины в нижнем регистре
        self.direction_number = direction_number  # Номер направления (0 = вправо, 1 = вниз и т.д.)
        self.direction = direction  # Текстовое значение направления движения ('right', 'down' и т.д.)

        # Устанавливаем начальные координаты машины (из предустановленных значений)
        self.x = simulation.x[direction][lane]
        self.y = simulation.y[direction][lane]

        # Связь с глобальными списками машин
        self.vehiclesTurned = simulation.vehiclesTurned  # Машины, которые повернули
        self.vehiclesNotTurned = simulation.vehiclesNotTurned  # Машины, которые поехали прямо

        # Границы стоп-линий (где машины должны остановиться)
        self.stopLines = simulation.stopLines

        # Глобальный список машин, распределённый по направлениям и полосам
        self.vehicles = simulation.vehicles

        # Флаги движения
        self.crossed = 0  # Флаг: пересекла ли машина перекрёсток
        self.willTurn = will_turn  # Флаг: собирается ли машина повернуть
        self.turned = 0  # Флаг: повернула ли машина
        self.rotateAngle = 0  # Угол поворота машины
        self.rotationAngle = 3  # Скорость поворота машины

        # Минимальный зазор между машинами (используется для остановки)
        self.movingGap = simulation.movingGap

        # Добавляем машину в список машин на данном направлении и полосе
        self.vehicles[direction][lane].append(self)
        self.index = len(simulation.vehicles[direction][lane]) - 1  # Индекс в списке машин
        self.crossedIndex = 0  # Индекс в списке пересечённых машин

        # Загружаем изображение машины на основе её направления и типа
        path = "images/" + direction + "/" + self.vehicleClass + ".png"
        self.originalImage = pygame.image.load(path)
        self.image = self.originalImage.copy()

        # --- Определение точки остановки машины перед перекрёстком ---
        if (len(simulation.vehicles[direction][lane]) > 1 and
                simulation.vehicles[direction][lane][self.index - 1].crossed == 0):
            # Если есть предыдущая машина, устанавливаем остановку относительно неё
            prev_vehicle = simulation.vehicles[direction][lane][self.index - 1]
            if direction == 'right':
                self.stop = prev_vehicle.stop - prev_vehicle.image.get_rect().width - simulation.stoppingGap
            elif direction == 'left':
                self.stop = prev_vehicle.stop + prev_vehicle.image.get_rect().width + simulation.stoppingGap
            elif direction == 'down':
                self.stop = prev_vehicle.stop - prev_vehicle.image.get_rect().height - simulation.stoppingGap
            elif direction == 'up':
                self.stop = prev_vehicle.stop + prev_vehicle.image.get_rect().height + simulation.stoppingGap
        else:
            # Если это первая машина, она останавливается на стандартной точке
            self.stop = simulation.defaultStop[direction]

        # --- Корректируем координаты для новой машины (чтобы она не накладывалась на предыдущие) ---
        if direction == 'right':
            temp = self.image.get_rect().width + simulation.stoppingGap
            simulation.x[direction][lane] -= temp  # Двигаем назад, чтобы оставить место
        elif direction == 'left':
            temp = self.image.get_rect().width + simulation.stoppingGap
            simulation.x[direction][lane] += temp  # Двигаем вперёд
        elif direction == 'down':
            temp = self.image.get_rect().height + simulation.stoppingGap
            simulation.y[direction][lane] -= temp  # Двигаем вверх
        elif direction == 'up':
            temp = self.image.get_rect().height + simulation.stoppingGap
            simulation.y[direction][lane] += temp  # Двигаем вниз

        # Добавляем машину в симуляцию (в группу спрайтов Pygame)
        simulation.simulation.add(self)

    def render(self, screen):
        """Рисование транспорта"""
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        """Управляет транспортом"""
        if (self.direction == 'right'):
            # --- Проверяем, пересекла ли машина стоп-линию ---
            if self.crossed == 0 and self.x + self.image.get_rect().width > self.stopLines[self.direction]:
                self.crossed = 1  # Устанавливаем флаг пересечения
                self.vehicles[self.direction]['crossed'] += 1  # Увеличиваем счётчик пересечённых машин

                if self.willTurn == 0:  # Если машина НЕ будет поворачивать
                    self.vehiclesNotTurned[self.direction][self.lane].append(
                        self)  # Добавляем её в список прямого движения
                    self.crossedIndex = len(self.vehiclesNotTurned[self.direction][self.lane]) - 1  # Индекс в списке

            # --- Обрабатываем случаи поворота ---
            if self.willTurn == 1:
                if self.lane == 1:  # Если машина находится в первой полосе (lane 1)
                    if self.crossed == 0 or self.x + self.image.get_rect().width < self.stopLines[self.direction] + 40:
                        # Проверяем условия движения до зоны поворота
                        if ((self.x + self.image.get_rect().width <= self.stop or
                             (
                                     self.simulation.currentGreen == 0 and self.simulation.currentYellow == 0) or self.crossed == 1) and
                                (self.index == 0 or self.x + self.image.get_rect().width <
                                 (self.vehicles[self.direction][self.lane][self.index - 1].x - self.movingGap) or
                                 self.vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                            self.x += self.speed  # Машина движется вправо
                    else:
                        if (self.turned == 0):
                            # Поворачиваем машину
                            self.rotateAngle += self.rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x += 2.4
                            self.y -= 2.8
                            if (self.rotateAngle == 90):
                                self.turned = 1
                                self.vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(self.vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if (self.crossedIndex == 0 or (self.y > (
                                    self.vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].y +
                                    self.vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1].image.get_rect().height + self.movingGap))):
                                self.y -= self.speed

                elif (self.lane == 2):
                    if (self.crossed == 0 or self.x + self.image.get_rect().width < self.simulation.mid[self.direction]['x']):
                        if ((self.x + self.image.get_rect().width <= self.stop or (
                                self.simulation.currentGreen == 0 and self.simulation.currentYellow == 0) or self.crossed == 1) and (
                                self.index == 0 or self.x + self.image.get_rect().width < (
                                self.vehicles[self.direction][self.lane][self.index - 1].x - self.movingGap) or
                                self.vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                            self.x += self.speed
                    else:
                        if (self.turned == 0):
                            self.rotateAngle += self.rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x += 2
                            self.y += 1.8
                            if (self.rotateAngle == 90):
                                self.turned = 1
                                self.vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(self.vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if (self.crossedIndex == 0 or ((self.y + self.image.get_rect().height) < (
                                    self.vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].y - self.movingGap))):
                                self.y += self.speed
            else:
                # --- Если машина НЕ поворачивает, она просто едет вперёд ---
                if (self.crossed == 0):
                    if ((self.x + self.image.get_rect().width <= self.stop or (
                            self.simulation.currentGreen == 0 and self.simulation.currentYellow == 0)) and (
                            self.index == 0 or self.x + self.image.get_rect().width < (
                            self.vehicles[self.direction][self.lane][self.index - 1].x - self.movingGap))):
                        self.x += self.speed
                else:
                    if ((self.crossedIndex == 0) or (self.x + self.image.get_rect().width < (
                            self.vehiclesNotTurned[self.direction][self.lane][self.crossedIndex - 1].x - self.movingGap))):
                        self.x += self.speed

        elif (self.direction == 'down'):
            if (self.crossed == 0 and self.y + self.image.get_rect().height > self.stopLines[self.direction]):
                self.crossed = 1
                self.vehicles[self.direction]['crossed'] += 1
                if (self.willTurn == 0):
                    self.vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(self.vehiclesNotTurned[self.direction][self.lane]) - 1
            if (self.willTurn == 1):
                if (self.lane == 1):
                    if (self.crossed == 0 or self.y + self.image.get_rect().height < self.stopLines[self.direction] + 50):
                        if ((self.y + self.image.get_rect().height <= self.stop or (
                                self.simulation.currentGreen == 1 and self.simulation.currentYellow == 0) or self.crossed == 1) and (
                                self.index == 0 or self.y + self.image.get_rect().height < (
                                self.vehicles[self.direction][self.lane][self.index - 1].y - self.movingGap) or
                                self.vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                            self.y += self.speed
                    else:
                        if (self.turned == 0):
                            self.rotateAngle += self.rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x += 1.2
                            self.y += 1.8
                            if (self.rotateAngle == 90):
                                self.turned = 1
                                self.vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(self.vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if (self.crossedIndex == 0 or ((self.x + self.image.get_rect().width) < (
                                    self.vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].x - self.movingGap))):
                                self.x += self.speed
                elif (self.lane == 2):
                    if (self.crossed == 0 or self.y + self.image.get_rect().height < self.simulation.mid[self.direction]['y']):
                        if ((self.y + self.image.get_rect().height <= self.stop or (
                                self.simulation.currentGreen == 1 and self.simulation.currentYellow == 0) or self.crossed == 1) and (
                                self.index == 0 or self.y + self.image.get_rect().height < (
                                self.vehicles[self.direction][self.lane][self.index - 1].y - self.movingGap) or
                                self.vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                            self.y += self.speed
                    else:
                        if (self.turned == 0):
                            self.rotateAngle += self.rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x -= 2.5
                            self.y += 2
                            if (self.rotateAngle == 90):
                                self.turned = 1
                                self.vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(self.vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if (self.crossedIndex == 0 or (self.x > (
                                    self.vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].x +
                                    self.vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1].image.get_rect().width + self.movingGap))):
                                self.x -= self.speed
            else:
                if (self.crossed == 0):
                    if ((self.y + self.image.get_rect().height <= self.stop or (
                            self.simulation.currentGreen == 1 and self.simulation.currentYellow == 0)) and (
                            self.index == 0 or self.y + self.image.get_rect().height < (
                            self.vehicles[self.direction][self.lane][self.index - 1].y - self.movingGap))):
                        self.y += self.speed
                else:
                    if ((self.crossedIndex == 0) or (self.y + self.image.get_rect().height < (
                            self.vehiclesNotTurned[self.direction][self.lane][self.crossedIndex - 1].y - self.movingGap))):
                        self.y += self.speed
        elif (self.direction == 'left'):
            if (self.crossed == 0 and self.x < self.stopLines[self.direction]):
                self.crossed = 1
                self.vehicles[self.direction]['crossed'] += 1
                if (self.willTurn == 0):
                    self.vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(self.vehiclesNotTurned[self.direction][self.lane]) - 1
            if (self.willTurn == 1):
                if (self.lane == 1):
                    if (self.crossed == 0 or self.x > self.stopLines[self.direction] - 70):
                        if ((self.x >= self.stop or (
                                self.simulation.currentGreen == 2 and self.simulation.currentYellow == 0) or self.crossed == 1) and (
                                self.index == 0 or self.x > (self.vehicles[self.direction][self.lane][self.index - 1].x +
                                                             self.vehicles[self.direction][self.lane][
                                                                 self.index - 1].image.get_rect().width + self.movingGap) or
                                self.vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                            self.x -= self.speed
                    else:
                        if (self.turned == 0):
                            self.rotateAngle += self.rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x -= 0.9
                            self.y += 1.2
                            if (self.rotateAngle == 90):
                                self.turned = 1
                                self.vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(self.vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if (self.crossedIndex == 0 or ((self.y + self.image.get_rect().height) < (
                                    self.vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].y - self.movingGap))):
                                self.y += self.speed
                elif (self.lane == 2):
                    if (self.crossed == 0 or self.x > self.simulation.mid[self.direction]['x']):
                        if ((self.x >= self.stop or (
                                self.simulation.currentGreen == 2 and self.simulation.currentYellow == 0) or self.crossed == 1) and (
                                self.index == 0 or self.x > (self.vehicles[self.direction][self.lane][self.index - 1].x +
                                                             self.vehicles[self.direction][self.lane][
                                                                 self.index - 1].image.get_rect().width + self.movingGap) or
                                self.vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                            self.x -= self.speed
                    else:
                        if (self.turned == 0):
                            self.rotateAngle += self.rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x -= 1.4
                            self.y -= 2.5
                            if (self.rotateAngle == 90):
                                self.turned = 1
                                self.vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(self.vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if (self.crossedIndex == 0 or (self.y > (
                                    self.vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].y +
                                    self.vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1].image.get_rect().height + self.movingGap))):
                                self.y -= self.speed
            else:
                if (self.crossed == 0):
                    if ((self.x >= self.stop or (self.simulation.currentGreen == 2 and self.simulation.currentYellow == 0)) and (
                            self.index == 0 or self.x > (
                            self.vehicles[self.direction][self.lane][self.index - 1].x + self.vehicles[self.direction][self.lane][
                        self.index - 1].image.get_rect().width + self.movingGap))):
                        self.x -= self.speed
                else:
                    if ((self.crossedIndex == 0) or (self.x > (
                            self.vehiclesNotTurned[self.direction][self.lane][self.crossedIndex - 1].x +
                            self.vehiclesNotTurned[self.direction][self.lane][
                                self.crossedIndex - 1].image.get_rect().width + self.movingGap))):
                        self.x -= self.speed

        elif (self.direction == 'up'):
            if (self.crossed == 0 and self.y < self.stopLines[self.direction]):
                self.crossed = 1
                self.vehicles[self.direction]['crossed'] += 1
                if (self.willTurn == 0):
                    self.vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(self.vehiclesNotTurned[self.direction][self.lane]) - 1
            if (self.willTurn == 1):
                if (self.lane == 1):
                    if (self.crossed == 0 or self.y > self.stopLines[self.direction] - 60):
                        if ((self.y >= self.stop or (
                                self.simulation.currentGreen == 3 and self.simulation.currentYellow == 0) or self.crossed == 1) and (
                                self.index == 0 or self.y > (self.vehicles[self.direction][self.lane][self.index - 1].y +
                                                             self.vehicles[self.direction][self.lane][
                                                                 self.index - 1].image.get_rect().height + self.movingGap) or
                                self.vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                            self.y -= self.speed
                    else:
                        if (self.turned == 0):
                            self.rotateAngle += self.rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x -= 2
                            self.y -= 1.2
                            if (self.rotateAngle == 90):
                                self.turned = 1
                                self.vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(self.vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if (self.crossedIndex == 0 or (self.x > (
                                    self.vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].x +
                                    self.vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1].image.get_rect().width + self.movingGap))):
                                self.x -= self.speed
                elif (self.lane == 2):
                    if (self.crossed == 0 or self.y > self.simulation.mid[self.direction]['y']):
                        if ((self.y >= self.stop or (
                                self.simulation.currentGreen == 3 and self.simulation.currentYellow == 0) or self.crossed == 1) and (
                                self.index == 0 or self.y > (self.vehicles[self.direction][self.lane][self.index - 1].y +
                                                             self.vehicles[self.direction][self.lane][
                                                                 self.index - 1].image.get_rect().height + self.movingGap) or
                                self.vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                            self.y -= self.speed
                    else:
                        if (self.turned == 0):
                            self.rotateAngle += self.rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x += 1
                            self.y -= 1
                            if (self.rotateAngle == 90):
                                self.turned = 1
                                self.vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(self.vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if (self.crossedIndex == 0 or (self.x < (
                                    self.vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].x -
                                    self.vehiclesTurned[self.direction][self.lane][
                                        self.crossedIndex - 1].image.get_rect().width - self.movingGap))):
                                self.x += self.speed
            else:
                if (self.crossed == 0):
                    if ((self.y >= self.stop or (self.simulation.currentGreen == 3 and self.simulation.currentYellow == 0)) and (
                            self.index == 0 or self.y > (
                            self.vehicles[self.direction][self.lane][self.index - 1].y + self.vehicles[self.direction][self.lane][
                        self.index - 1].image.get_rect().height + self.movingGap))):
                        self.y -= self.speed
                else:
                    if ((self.crossedIndex == 0) or (self.y > (
                            self.vehiclesNotTurned[self.direction][self.lane][self.crossedIndex - 1].y +
                            self.vehiclesNotTurned[self.direction][self.lane][
                                self.crossedIndex - 1].image.get_rect().height + self.movingGap))):
                        self.y -= self.speed


class Car(Vehicle):
    def __init__(self, speed, lane, direction_number, direction, will_turn, simulation):
        """Инициализация машины"""
        super().__init__(speed, lane, direction_number, direction, will_turn, simulation)

        path = "images/" + direction + "/" + "car" + ".png"
        self.image = pygame.image.load(path)



class Truck(Vehicle):
    def __init__(self, speed, lane, direction_number, direction, will_turn, simulation):
        """Инициализация грузовика"""
        super().__init__(speed, lane, direction_number, direction, will_turn, simulation)

        path = "images/" + direction + "/" + "truck" + ".png"
        self.image = pygame.image.load(path)


class Bike(Vehicle):
    def __init__(self, speed, lane, direction_number, direction, will_turn, simulation):
        """Инициализация мотоцикла"""
        super().__init__(speed, lane, direction_number, direction, will_turn, simulation)

        path = "images/" + direction + "/" + "bike" + ".png"
        self.image = pygame.image.load(path)