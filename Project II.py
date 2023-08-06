import simpy

SIM_TIME = 100000
BUFFER_CAPACITY = 5


class PackagingLine:
    def __init__(self, env):
        self.env = env
        self.items = 0
        self.filling_queue = simpy.Store(env)
        self.capping_queue = simpy.Store(env)
        self.labeling_queue = simpy.Store(env)
        self.sealing_queue = simpy.Store(env)
        self.carton_packing_queue = simpy.Store(env)

        self.filling_time = 6.5
        self.capping_time = 5
        self.labeling_time = 8
        self.sealing_time = 5
        self.carton_packing_time = 6

        self.filling_blocked = 0
        self.capping_blocked = 0
        self.labeling_blocked = 0
        self.sealing_blocked = 0

    def fill(self, unit):
        yield self.env.timeout(self.filling_time)

        yield self.capping_queue.put(unit)
        print('Unit capping started')

    def cap(self, unit):
        yield self.env.timeout(self.capping_time)
        print('Unit capping finished -->')

        yield self.labeling_queue.put(unit)
        print('Unit labeling started')

    def label(self, unit):
        yield self.env.timeout(self.labeling_time)
        print('Unit labeling finished -->')

        yield self.sealing_queue.put(unit)
        print('Unit sealing started')

    def seal(self, unit):
        yield self.env.timeout(self.sealing_time)
        print('Unit sealing finished -->')

        yield self.carton_packing_queue.put(unit)
        print('Unit packing started')

    def pack(self, unit):
        yield self.env.timeout(self.carton_packing_time)
        print('Unit packing finished --|')

    def generate_items(self):
        while True:
            # Generate a new item every 10 time units
            yield self.env.timeout(10)
            self.items += 1
            print('Generated new item:',)
            yield self.filling_queue.put(self.items)

    
    def run(self):
        self.env.process(self.generate_items())

        while True:
            try:
                unit = yield self.filling_queue.get()
                self.env.process(self.fill(unit))
            except simpy.Interrupt:
                self.filling_blocked += 1

            try:
                unit = yield self.capping_queue.get()
                self.env.process(self.cap(unit))
            except simpy.Interrupt:
                self.capping_blocked += 1

            try:
                unit = yield self.labeling_queue.get()
                self.env.process(self.label(unit))
            except simpy.Interrupt:
                self.labeling_blocked += 1

            try:
                unit = yield self.sealing_queue.get()
                self.env.process(self.seal(unit))
            except simpy.Interrupt:
                self.sealing_blocked += 1

            unit = yield self.carton_packing_queue.get()
            self.env.process(self.pack(unit))


env = simpy.Environment()
packaging_line = PackagingLine(env)
env.process(packaging_line.run())
env.run(until=SIM_TIME)

throughput = packaging_line.items / (SIM_TIME / 3600)
avg_inventory = (
    sum(len(q.items) for q in [
        packaging_line.filling_queue,
        packaging_line.capping_queue,
        packaging_line.labeling_queue,
        packaging_line.sealing_queue,
        packaging_line.carton_packing_queue]) / 5)
downtime_probabilities = {
    'filling': packaging_line.filling_blocked / SIM_TIME,
    'capping': packaging_line.capping_blocked / SIM_TIME,
    'labeling': packaging_line.labeling_blocked / SIM_TIME,
    'sealing': packaging_line.sealing_blocked / SIM_TIME,
}


print("Throughput: {} units/hr".format(throughput))
print("Average inventory levels in buffers: {:.2f}".format(avg_inventory))
print("Downtime probabilities:")
for workstation, prob in downtime_probabilities.items():
    print("- {}: {:.2%}".format(workstation, prob))
