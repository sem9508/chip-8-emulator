import time
import pygame
import random

pygame.init()
pygame.mixer.init()

class VideoSystem:
    def __init__(self, width, height, scale):
        self.width, self.height = width, height
        self.scale = scale
        self.screen = pygame.display.set_mode((width*scale, height*scale))

        self.clear()

        
    def clear(self):
        self.screen.fill('black')
        pygame.display.flip()

class CPU:
    def __init__(self, vf_reset, memory_i_inc):
        self.run = True
        self.memory = [0] * 4096
        self.start_address = 0x200
        self.rom_size = None

        self.vf_reset = vf_reset
        self.memory_i_inc = memory_i_inc        

        self.fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,
            0x20, 0x60, 0x20, 0x20, 0x70,
            0xF0, 0x10, 0xF0, 0x80, 0xF0,
            0xF0, 0x10, 0xF0, 0x10, 0xF0,
            0x90, 0x90, 0xF0, 0x10, 0x10,
            0xF0, 0x80, 0xF0, 0x10, 0xF0,
            0xF0, 0x80, 0xF0, 0x90, 0xF0,
            0xF0, 0x10, 0x20, 0x40, 0x40,
            0xF0, 0x90, 0xF0, 0x90, 0xF0,
            0xF0, 0x90, 0xF0, 0x10, 0xF0,
            0xF0, 0x90, 0xF0, 0x90, 0x90,
            0xE0, 0x90, 0xE0, 0x90, 0xE0,
            0xF0, 0x80, 0x80, 0x80, 0xF0,
            0xE0, 0x90, 0x90, 0x90, 0xE0,
            0xF0, 0x80, 0xF0, 0x80, 0xF0,
            0xF0, 0x80, 0xF0, 0x80, 0x80 
        ]

        self.key_map = {
            pygame.K_x: 0x0,  # 0
            pygame.K_1: 0x1,  # 1
            pygame.K_2: 0x2,  # 2
            pygame.K_3: 0x3,  # 3
            pygame.K_q: 0x4,  # 4
            pygame.K_w: 0x5,  # 5
            pygame.K_e: 0x6,  # 6
            pygame.K_a: 0x7,  # 7
            pygame.K_s: 0x8,  # 8
            pygame.K_d: 0x9,  # 9
            pygame.K_z: 0xA,  # A
            pygame.K_c: 0xB,  # B
            pygame.K_4: 0xC,  # C
            pygame.K_r: 0xD,  # D
            pygame.K_f: 0xE,  # E
            pygame.K_v: 0xF   # F
        }

        for i, byte in enumerate(self.fontset):
            self.memory[0x50 + i] = byte


        self.stack = []

        self.skip_next_instruction = False

        self.videosystem = VideoSystem(64, 32, 10)

        self.V = [0]*16
        self.I = self.start_address     # INDEX POINTER
        self.PC = self.start_address    # PROGRAM COUNTER
        self.SP = 0                     # STACK POINTER
        self.DT = 0                     # DELAY TIMER
        self.ST = 0                     # SOUND TIMER

        self.sprite_width = 8

    def load_rom(self, path):
        with open(path, 'rb') as file:
            file_rom = file.read()
            for i, byte in enumerate(file_rom):
                self.memory[self.start_address + i] = byte
            self.rom_size = len(file_rom)

    def get_pressed_chip8_keys(self):
        keys = pygame.key.get_pressed()
        pressed = []
        for key, chip8_val in self.key_map.items():
            if keys[key]:
                pressed.append(chip8_val)
        return pressed

    def get_opcode(self):
        return (self.memory[self.PC] << 8) + self.memory[self.PC+1]

    def get_x(self, opcode):
        return (opcode&0x0F00) >> 8
    
    def get_y(self, opcode):
        return (opcode&0x00F0) >> 4
    
    def get_n(self, opcode):
        return opcode&0x000F

    def get_nn(self, opcode):
        return opcode&0x00FF
    
    def get_nnn(self, opcode):
        return opcode&0x0FFF
    
    def maskV(self, index):
        self.V[index] = self._mask8(self.V[index])
    
    def draw_sprite(self, x, y, height):
        self.V[0xF] = 0
        for sprite_y in range(height):
            pixel_row = format(self.memory[self.I+sprite_y], '08b')
            for sprite_x in range(self.sprite_width):
                if int(pixel_row[sprite_x]) == 1:
                    pixel_pos_x = self.videosystem.scale*x+self.videosystem.scale*sprite_x
                    pixel_pos_y = self.videosystem.scale*y+self.videosystem.scale*sprite_y

                    while pixel_pos_x >= self.videosystem.scale*self.videosystem.width:
                        pixel_pos_x -= self.videosystem.scale*self.videosystem.width

                    while pixel_pos_y >= self.videosystem.scale*self.videosystem.height:
                        pixel_pos_y -= self.videosystem.scale*self.videosystem.height

                    if self.videosystem.screen.get_at((pixel_pos_x, pixel_pos_y)) == (0, 0, 0, 255):
                        pygame.draw.rect(self.videosystem.screen, 'white', (pixel_pos_x, pixel_pos_y, self.videosystem.scale, self.videosystem.scale))
                    else:
                        pygame.draw.rect(self.videosystem.screen, 'black', (pixel_pos_x, pixel_pos_y, self.videosystem.scale, self.videosystem.scale))
                        self.V[0xF] = 1
        pygame.display.update()

       
    def execute_opcode(self, opcode):
        # STARTING WITH 0
        if opcode == 0x0000:
            self.increment_pc()
        elif opcode == 0x00E0:
            # print('clear screen')
            self.videosystem.clear()
            self.increment_pc()
        elif opcode == 0x00EE:
            # print('returns form a subroutine')
            self.PC = self.stack.pop()
        elif opcode & 0xF000 == 0x0000:
            # print('Calls machine code routine (RCA 1802 for COSMAC VIP) at address NNN. Not necessary for most ROMs.')
            print(f'Ignored ONNN opcode at {hex(opcode)}')
            self.increment_pc()

        # STARTING WITH 1
        elif opcode & 0xF000 == 0x1000:
            # print(f'jumps to addresss {hex(opcode&0x0FFF)}')
            self.PC = self.get_nnn(opcode)

        # STARTING WITH 2
        elif opcode & 0xF000 == 0x2000:
            # print(f'calls subroutine at {hex(opcode&0x0FFF)}')
            self.stack.append(self.PC+2)
            self.PC = self.get_nnn(opcode)

        # STARTING WITH 3
        elif opcode & 0xF000 == 0x3000:
            # print('skips the next instruction if VX equals NN. (usually the next instruction is  a jump to skip a code block)')
            if self.V[self.get_x(opcode)] == self.get_nn(opcode):
                self.skip_next_instruction = True
            self.increment_pc()

        # STARTING WITH 4
        elif opcode & 0xF000 == 0x4000:
            # print('Skips the next instruction if VX does not equal NN. (Usually the next instruction is a jump to skip a code block);')
            if self.V[self.get_x(opcode)] != self.get_nn(opcode):
                self.skip_next_instruction = True
            self.increment_pc()

        # STARTING WITH 5
        elif opcode & 0xF00F == 0x5000:
            # print('Skips the next instruction if VX equals VY. (Usually the next instruction is a jump to skip a code block);')
            if self.V[self.get_x(opcode)] == self.V[self.get_y(opcode)]:
                self.skip_next_instruction = True
            self.increment_pc()

        # STARTING WITH 6
        elif opcode & 0xF000 == 0x6000:
            # print('Sets VX to NN.')
            self.V[self.get_x(opcode)] = self.get_nn(opcode)
            self.increment_pc()

        # STARTING WITH 7
        elif opcode & 0xF000 == 0x7000:
            # print('Adds NN to VX. (Carry flag is not changed);')
            self.V[self.get_x(opcode)] += self.get_nn(opcode)
            self.maskV(self.get_x(opcode))
            self.increment_pc()
        
        # STARTING WITH 8
        elif opcode & 0xF00F == 0x8000:
            #print('Sets VX to the value of VY.')
            self.V[self.get_x(opcode)] = self.V[self.get_y(opcode)]
            self.increment_pc()
        elif opcode & 0xF00F == 0x8001:
            #print('Sets VX to VX or VY. (Bitwise OR operation);')
            if self.vf_reset:
                self.V[0xF] = 0

            x = self.get_x(opcode)
            y = self.get_y(opcode)

            self.V[x] = self.V[x] | self.V[y]

            self.increment_pc()
        elif opcode & 0xF00F == 0x8002:
            #print('Sets VX to VX and VY. (Bitwise AND operation);')
            if self.vf_reset:
                self.V[0xF] = 0

            x = self.get_x(opcode)
            y = self.get_y(opcode)

            self.V[x] = self.V[x] & self.V[y]
            
            self.increment_pc()
        elif opcode & 0xF00F == 0x8003:
            #print('Sets VX to VX xor VY.')
            if self.vf_reset:
                self.V[0xF] = 0

            x = self.get_x(opcode)
            y = self.get_y(opcode)

            self.V[x] = self.V[x] ^ self.V[y]
            self.increment_pc()
        elif opcode & 0xF00F == 0x8004:
            #print('Adds VY to VX. VF is set to 1 when theres a carry, and to 0 when there is not.')
            x = self.get_x(opcode)
            y = self.get_y(opcode)

            total = self.V[x] + self.V[y]
            self.V[x] = total & 0xFF
            self.V[0xF] = 1 if total > 0xFF else 0  # Set VF if carry

            self.increment_pc()
        elif opcode & 0xF00F == 0x8005:
            #print('VY is subtracted from VX. VF is set to 0 when theres a borrow, and 1 when there is not.')
            x = self.get_x(opcode)
            y = self.get_y(opcode)
            no_borrow = self.V[x] >= self.V[y]
            self.V[x] = (self.V[x] - self.V[y]) & 0xFF
            self.V[0xF] = 1 if no_borrow else 0  # No borrow -> VF = 1

            self.increment_pc() 
        elif opcode & 0xF00F == 0x8006:
            #print('	Stores the least significant bit of VX in VF and then shifts VX to the right by 1.[b]')
            x = self.get_x(opcode)
            flag = self.V[x] & 0x1
            self.V[x] >>= 1
            self.V[0xF] = flag
            self.increment_pc()
        elif opcode & 0xF00F == 0x8007:
            #print('Sets VX to VY minus VX. VF is set to 0 when theres a borrow, and 1 when there is not.')
            x = self.get_x(opcode)
            y = self.get_y(opcode)
            no_borrow = self.V[x] <= self.V[y]
            self.V[x] = (self.V[y] - self.V[x]) & 0xFF
            self.V[0xF] = 1 if no_borrow else 0  # No borrow -> VF = 1

            self.increment_pc() 
        elif opcode & 0xF00F == 0x800E:
            #print('Stores the most significant bit of VX in VF and then shifts VX to the left by 1.[b]')
            x = self.get_x(opcode)
            flag = (self.V[x] & 0x80) >> 7
            self.V[x] = (self.V[x] << 1) & 0xFF
            self.V[0xF] = flag
            self.increment_pc()

        # STARTING WITH 9
        elif opcode & 0xF00F == 0x9000:
            # print('Skips the next instruction if VX does not equal VY. (Usually the next instruction is a jump to skip a code block);')
            if self.V[self.get_x(opcode)] != self.V[self.get_y(opcode)]:
                self.skip_next_instruction = True
            self.increment_pc()

        # STARTING WITH A
        elif opcode & 0xF000 == 0xA000:
            # print(f'sets I to the address {hex(opcode&0x0FFF)}')
            self.I = self.get_nnn(opcode)
            self.increment_pc()
        
        # STARTING WITH B
        elif opcode & 0xF000 == 0xB000:
            # print(f'jumps to the address {hex(opcode&0x0FFF)} plus V0')
            self.PC = self.get_nnn(opcode) + self.V[0]
        
        # STARTING WITH C
        elif opcode & 0xF000 == 0xC000:
            # print('sets VX to the result of a bitwise and operation on a random number (typically 0 to 255) and NN')
            self.V[self.get_x(opcode)] = random.randint(0, 255)&self.get_nn(opcode)
            self.maskV(self.get_x(opcode))
            self.increment_pc()
        
        # STARTING WITH D
        elif opcode & 0xF000 == 0xD000:
            # print('Draws a sprite at coordinate (VX, VY) that has a width of 8 pixels and a height of N pixels. Each row of 8 pixels is read as bit-coded starting from memory location I; I value does not change after the execution of this instruction. As described above, VF is set to 1 if any screen pixels are flipped from set to unset when the sprite is drawn, and to 0 if that does not happen')
            x = self.V[self.get_x(opcode)]
            y = self.V[self.get_y(opcode)]

            n = self.get_n(opcode)
            self.draw_sprite(x, y, n)
            self.increment_pc()


        # STARTING WITH E
        elif opcode & 0xF0FF == 0xE09E:
            #print('Skips the next instruction if the key stored in VX is pressed. (Usually the next instruction is a jump to skip a code block);')
            if self.V[self.get_x(opcode)] in cpu.get_pressed_chip8_keys():
                self.skip_next_instruction = True
            self.increment_pc()

        elif opcode & 0xF0FF == 0xE0A1:
            #print('Skips the next instruction if the key stored in VX is not pressed. (Usually the next instruction is a jump to skip a code block);')
            if self.V[self.get_x(opcode)] not in cpu.get_pressed_chip8_keys():
                self.skip_next_instruction = True
            self.increment_pc()

        # STARTING WITH F
        elif opcode & 0xF0FF == 0xF007:
            #print('Sets VX to the value of the delay timer.')
            self.V[self.get_x(opcode)] = self.DT
            self.increment_pc()
        elif opcode & 0xF0FF == 0xF00A:
            #print('A key press is awaited, and then stored in VX. (Blocking Operation. All instruction halted until next key event);')

            x = self.get_x(opcode)
            print('waiting for key press...')
            key_pressed = False
            key_released = False
            while not key_released:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        cpu.run = False
                        break
                    if event.type == pygame.KEYDOWN:
                        key = event.key
                        if key in self.key_map:
                            self.V[x] = self.key_map[key]
                            key_pressed = True
                            
                    if event.type == pygame.KEYUP and key_pressed:
                        key_released = True

                if cpu.DT > 0:
                    cpu.DT -= 1
                pygame.time.delay(10)
            self.increment_pc()
        elif opcode & 0xF0FF == 0xF015:
            #print('Sets the delay timer to VX.')
            self.DT = self.V[self.get_x(opcode)]
            self.increment_pc()
        elif opcode & 0xF0FF == 0xF018:
            #print('Sets the sound timer to VX.')
            self.ST = self.V[self.get_x(opcode)]
            self.increment_pc()
        elif opcode & 0xF0FF == 0xF01E:
            # print('Adds VX to I. VF is not affected.[c]')
            self.I += self.V[self.get_x(opcode)]
            self.increment_pc()
        elif opcode & 0xF0FF == 0xF029:
            # print('Sets I to the location of the sprite for the character in VX. Characters 0-F (in hexadecimal) are represented by a 4x5 font.')
            digit = self.V[self.get_x(opcode)]
            self.I = 0x50 + (digit * 5)
            self.increment_pc()
        elif opcode & 0xF0FF == 0xF033:
            #print('Stores the binary-coded decimal representation of VX, with the most significant of three digits at the address in I, the middle digit at I plus 1, and the least significant digit at I plus 2. (In other words, take the decimal representation of VX, place the hundreds digit in memory at location in I, the tens digit at location I+1, and the ones digit at location I+2.);')
            x = self.get_x(opcode)
            value = self.V[x]

            self.memory[self.I]     = value // 100        
            self.memory[self.I + 1] = (value // 10) % 10 
            self.memory[self.I + 2] = value % 10
            self.increment_pc() 
        elif opcode & 0xF0FF == 0xF055:
            #print('Stores from V0 to VX (including VX) in memory, starting at address I. The offset from I is increased by 1 for each value written, but I itself is left unmodified.[d]')
            x = self.get_x(opcode)

            for i in range(x+1):
                self.memory[self.I+i] = self.V[i]

            if self.memory_i_inc:
                self.I += x+1
            self.increment_pc()
        elif opcode & 0xF0FF == 0xF065:
            #print('Fills from V0 to VX (including VX) with values from memory, starting at address I. The offset from I is increased by 1 for each value written, but I itself is left unmodified.[d]')
            x = self.get_x(opcode)

            for i in range(x+1):
                self.V[i] = self.memory[self.I+i]

            if self.memory_i_inc:
                self.I += x+1

            self.increment_pc()

        # OPCODE NOT FOUND
        else:
            print(f'UNKNOWN OPCODE --- {hex(opcode)} --- UNKOWN OPCODE')
            self.increment_pc()

    def increment_pc(self):
        self.PC += 2
        if self.PC > len(self.memory)-1:
            self.run = False
        if self.PC >= self.start_address + self.rom_size + 1:
            self.run = False

    def _mask8(self, value):
        return value & 0xFF

    def print_memory(self):
        print(self.memory)


vf_reset = False
memory_i_inc = False

cpu = CPU(vf_reset, memory_i_inc)
cpu.load_rom('TETRIS')

clock = pygame.time.Clock()

sound = pygame.mixer.Sound('beep.mp3')
playing_sound = False

decrement_timers_timer = 1
decrement_timers = 8

while cpu.run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            cpu.run = False

    if not cpu.run:
        break

    opcode = cpu.get_opcode()


    cpu.execute_opcode(opcode)

    if cpu.skip_next_instruction:
        cpu.increment_pc()
        cpu.skip_next_instruction = False

    clock.tick(500)

    if decrement_timers_timer >= decrement_timers:
        if cpu.DT > 0:
            cpu.DT -= 1
        if cpu.ST > 0:
            if not playing_sound:
                sound.play(-1)
                playing_sound = True

            cpu.ST -= 1

        else:
            if playing_sound:
                sound.stop()
                playing_sound = False
        decrement_timers_timer = 1
    else:
        decrement_timers_timer += 1


