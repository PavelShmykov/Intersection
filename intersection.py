import random
import time
import threading
import pygame
from trafficsignal import TrafficSignal
from transport import Car, Bike, Truck

class Simulation:
    def __init__(self):
        self.clock = pygame.time.Clock()

        # Загрузка фона перекрёстка
        self.background = pygame.image.load('images/intersection.png')

        # Группа спрайтов для управления транспортом
        self.simulation = pygame.sprite.Group()

        # Начальные координаты транспортных средств для каждого направления
        self.x = {'right': [0, 0, 0], 'down': [755, 737, 705], 'left': [1400, 1400, 1400], 'up': [602, 634, 665]}
        self.y = {'right': [348, 370, 398], 'down': [0, 0, 0], 'left': [498, 466, 436], 'up': [800, 800, 800]}

        # Словарь для хранения машин по направлениям и полосам
        self.vehicles = {
            'right': {0: [], 1: [], 2: [], 'crossed': 0},
            'down': {0: [], 1: [], 2: [], 'crossed': 0},
            'left': {0: [], 1: [], 2: [], 'crossed': 0},
            'up': {0: [], 1: [], 2: [], 'crossed': 0}
        }

        # Координаты стоп-линий и стандартные точки остановки машин
        self.stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
        self.defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

        # Минимальное расстояние между машинами
        self.stoppingGap = 25
        self.movingGap = 25

        # Количество светофоров на перекрёстке
        self.noOfSignals = 4
        self.signals = []  # Список для хранения объектов светофоров

        # Переключение текущего зелёного сигнала
        self.currentGreen = 0
        self.nextGreen = (self.currentGreen + 1) % self.noOfSignals
        self.currentYellow = 0

        # Координаты отображения светофоров на экране
        self.signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
        self.signalTimerCoods = [(530, 210), (810, 210), (810, 550), (530, 550)]

        # Настройки продолжительности сигналов (по умолчанию)
        self.defaultGreen = {0: 10, 1: 10, 2: 10, 3: 10}
        self.defaultRed = 150
        self.defaultYellow = 5

        # Направления движения транспорта
        self.directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}

        # Списки повёрнутых и неповёрнутых машин
        self.vehiclesTurned = {'right': {1: [], 2: []}, 'down': {1: [], 2: []}, 'left': {1: [], 2: []},
                               'up': {1: [], 2: []}}
        self.vehiclesNotTurned = {'right': {1: [], 2: []}, 'down': {1: [], 2: []}, 'left': {1: [], 2: []},
                                  'up': {1: [], 2: []}}

        # Угол поворота машин
        self.rotationAngle = 3

        # Координаты середины перекрёстка для расчёта поворотов
        self.mid = {'right': {'x': 705, 'y': 445}, 'down': {'x': 695, 'y': 450},
                    'left': {'x': 695, 'y': 425}, 'up': {'x': 695, 'y': 400}}

        # Управление динамическим временем зелёного сигнала
        self.dinamicGreenSignalTimer = False
        self.dinamicGreenSignalTimerRange = [10, 20]

    def render(self):
        """Метод отрисовки всего содержимого экрана"""
        # Отрисовка фона
        self.screen.blit(self.background, (0, 0))

        # Отрисовка светофоров
        for i in range(self.noOfSignals):
            if i == self.currentGreen:
                if self.currentYellow == 1:
                    self.signals[i].signalText = self.signals[i].yellow
                    self.screen.blit(self.yellowSignal, self.signalCoods[i])
                else:
                    self.signals[i].signalText = self.signals[i].green
                    self.screen.blit(self.greenSignal, self.signalCoods[i])
            else:
                if self.signals[i].red <= 10:
                    self.signals[i].signalText = self.signals[i].red
                else:
                    self.signals[i].signalText = "---"
                self.screen.blit(self.redSignal, self.signalCoods[i])

        # Отрисовка таймеров сигналов
        for i in range(self.noOfSignals):
            text = self.font.render(str(self.signals[i].signalText), True, (255, 255, 255), (0, 0, 0))
            self.screen.blit(text, self.signalTimerCoods[i])

        # Отрисовка и обновление транспортных средств
        for vehicle in self.simulation:
            self.screen.blit(vehicle.image, (vehicle.x, vehicle.y))
            vehicle.move()



        pygame.display.update()
        self.clock.tick(60)

    def create_ts(self):
        """ Инициализация светофоров с заданными или случайными значениями времени работы."""
        minTime = self.dinamicGreenSignalTimerRange[0]
        maxTime = self.dinamicGreenSignalTimerRange[1]

        if self.dinamicGreenSignalTimer:
            ts1 = TrafficSignal(0, self.defaultYellow, random.randint(minTime, maxTime))
            self.signals.append(ts1)
            ts2 = TrafficSignal(ts1.red + ts1.yellow + ts1.green, self.defaultYellow, random.randint(minTime, maxTime))
            self.signals.append(ts2)
            ts3 = TrafficSignal(self.defaultRed, self.defaultYellow, random.randint(minTime, maxTime))
            self.signals.append(ts3)
            ts4 = TrafficSignal(self.defaultRed, self.defaultYellow, random.randint(minTime, maxTime))
            self.signals.append(ts4)

        else:
            ts1 = TrafficSignal(0, self.defaultYellow, self.defaultGreen[0])
            self.signals.append(ts1)
            ts2 = TrafficSignal(ts1.yellow + ts1.green, self.defaultYellow, self.defaultGreen[1])
            self.signals.append(ts2)
            ts3 = TrafficSignal(self.defaultRed, self.defaultYellow, self.defaultGreen[2])
            self.signals.append(ts3)
            ts4 = TrafficSignal(self.defaultRed, self.defaultYellow, self.defaultGreen[3])
            self.signals.append(ts4)

        self.repeat()

    def repeat(self):
        """
        Управляет переключением светофоров в симуляции.
        - Светофоры последовательно проходят фазы зелёного, жёлтого и красного сигналов.
        - Обновляет `self.currentGreen`, чтобы следующий сигнал стал зелёным.
        """

        # Пока зелёный сигнал активен, обновляем значения каждую секунду
        while self.signals[self.currentGreen].green > 0:
            self.update_values()  # Обновление данных таймеров
            time.sleep(1)

        # Переход в фазу жёлтого сигнала
        self.currentYellow = 1  # Устанавливаем, что сейчас жёлтый сигнал

        # Устанавливаем точку остановки автомобилей на текущем направлении
        for i in range(0, 3):  # Перебираем полосы 0, 1, 2
            for vehicle in self.vehicles[self.directionNumbers[self.currentGreen]][i]:
                vehicle.stop = self.defaultStop[self.directionNumbers[self.currentGreen]]

                # Пока жёлтый сигнал активен, обновляем каждую секунду
        while self.signals[self.currentGreen].yellow > 0:
            self.update_values()  # Обновление таймеров
            time.sleep(1)

        self.currentYellow = 0  # Завершаем жёлтую фазу

        # Переключаемся на новый зелёный интервал
        if self.dinamicGreenSignalTimer:
            # Если используем случайные таймеры, выбираем случайное время зелёного сигнала
            self.signals[self.currentGreen].green = random.randint(self.dinamicGreenSignalTimerRange[0],
                                                                   self.dinamicGreenSignalTimerRange[1])
        else:
            # Используем фиксированные значения по умолчанию
            self.signals[self.currentGreen].green = self.defaultGreen[self.currentGreen]

        # Обновляем значения жёлтого и красного сигналов
        self.signals[self.currentGreen].yellow = self.defaultYellow
        self.signals[self.currentGreen].red = self.defaultRed

        # Переключаем текущий зелёный сигнал на следующий
        self.currentGreen = self.nextGreen
        self.nextGreen = (self.currentGreen + 1) % self.noOfSignals  # Вычисляем следующий светофор

        # Обновляем красный сигнал для следующего светофора
        self.signals[self.nextGreen].red = self.signals[self.currentGreen].yellow + self.signals[
            self.currentGreen].green
        self.repeat()

    def update_values(self):
        """
        Обновляет значения таймеров светофоров каждую секунду:
        - Если светофор зелёный (`self.currentGreen`), уменьшается время его зелёного или жёлтого сигнала.
        - Если светофор НЕ зелёный, уменьшается время его красного сигнала.
        """
        for i in range(0, self.noOfSignals):  # Перебираем все светофоры
            if i == self.currentGreen:  # Проверяем, является ли этот светофор текущим зелёным
                if self.currentYellow == 0:  # Если сейчас НЕ жёлтый сигнал
                    self.signals[i].green -= 1  # Уменьшаем оставшееся время зелёного света
                else:  # Если сейчас жёлтый сигнал
                    self.signals[i].yellow -= 1  # Уменьшаем оставшееся время жёлтого света
            else:
                self.signals[i].red -= 1  # Уменьшаем оставшееся время красного света для остальных светофоров

    def generate_vehicles(self):
        """Генерация транспорта"""
        while True:
            vehicle_type = random.choice([Car, Truck, Bike])
            lane_number = random.randint(1, 2)
            speed_kmh = random.randint(80, 120)
            speed_pix = speed_kmh / 30
            will_turn = random.randint(0, 1)
            direction_number = random.randint(0, 3)
            direction = self.directionNumbers[direction_number]


            vehicle = vehicle_type(speed_pix, lane_number, direction_number, direction, will_turn, self)
            self.vehicles[direction][lane_number].append(vehicle)
            self.simulation.add(vehicle)
            time.sleep(1.5)




    def run(self):
        """Запуск моделирования"""
        # Инициализация Pygame и создание окна
        pygame.init()
        self.screenWidth = 1400
        self.screenHeight = 800
        self.screen = pygame.display.set_mode((self.screenWidth, self.screenHeight))

        # Загрузка изображений светофоров
        self.redSignal = pygame.image.load('images/signals/red.png')
        self.yellowSignal = pygame.image.load('images/signals/yellow.png')
        self.greenSignal = pygame.image.load('images/signals/green.png')

        # Настройки шрифта для отображения таймеров
        self.font = pygame.font.Font(None, 30)

        # Запускаем потоки для генерации транспортных средств и инициализации светофоров
        thread_init = threading.Thread(target=self.create_ts, daemon=True)
        thread_init.start()
        thread_generate = threading.Thread(target=self.generate_vehicles, daemon=True)
        thread_generate.start()

        # Основной цикл отрисовки
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()

            self.render()

s = Simulation()
s.run()