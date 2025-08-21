from emulator import CPU, VideoSystem, emu_width, emu_height, emu_scale
import pygame
import os

pygame.init()
pygame.mixer.init()

class Button:
    def __init__(self, x, y, width, height, text, bg_color, txt_color, selected_color, script_name):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text

        self.script_name = script_name

        self.bg_color = bg_color
        self.txt_color = txt_color
        self.selected_color = selected_color
        self.current_color = self.bg_color

        self.font = pygame.font.SysFont('Arial', 16)
        self.text_surface = self.font.render(self.text, True, self.txt_color)


    def draw(self, screen:pygame.surface.Surface):
        pygame.draw.rect(screen, self.current_color, self.rect)
        screen.blit(self.text_surface, self.rect)

    def update(self, mouse, mouse_click):
        if self.rect.collidepoint(mouse[0], mouse[1]):
            self.current_color = self.selected_color
            if mouse_click:
                return True
        else:
            self.current_color = self.bg_color



class Launcher:
    def __init__(self):
        self.screen = pygame.display.set_mode((emu_width*emu_scale, emu_height*emu_scale))
        self.screen_width, self.screen_height = self.screen.get_width(), self.screen.get_height()

        self.run = True

        self.clock = pygame.time.Clock()


    def launch_type_menu_loop(self):
        buttons = []

        games_button = Button(50, 50, 200, 50, 'Games', (10, 10, 40), (0, 255, 220), (0, 0, 30), '/games')
        tests_button = Button(50, 150, 200, 50, 'Tests', (10, 10, 40), (0, 255, 220), (0, 0, 30), '/tests')
        
        buttons.append(games_button)
        buttons.append(tests_button)


        mouse_clicked = False
        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                    break

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_clicked = True
                if event.type == pygame.MOUSEBUTTONUP:
                    mouse_clicked = False

                if event.type == pygame.MOUSEWHEEL:
                    for button in buttons:
                        button.rect.y += event.y*20

            for button in buttons:
                if button.update(pygame.mouse.get_pos(), mouse_clicked):
                    script_name = button.script_name
                    if script_name[0] == '/':
                        return script_name[1:]
                    else:
                        print('why script in menu?')


            self.screen.fill((30, 30, 60))
            for button in buttons:
                button.draw(self.screen)
            pygame.display.update()
            self.clock.tick(60)

    def select_script_loop(self, folder):
        buttons = []
        i = 0

        for f in os.listdir(folder):
            if os.path.isfile(os.path.join(folder, f)):
                buttons.append(Button(50, 50+i*100, self.screen_width-100, 50, f, (10, 10, 40), (0, 255, 220), (0, 0, 30), f))

                i += 1

        mouse_clicked = False
        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                    break

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_clicked = True
                if event.type == pygame.MOUSEBUTTONUP:
                    mouse_clicked = False

                if event.type == pygame.MOUSEWHEEL:
                    for button in buttons:
                        button.rect.y += event.y*20

            for button in buttons:
                if button.update(pygame.mouse.get_pos(), mouse_clicked):
                    script_name = button.script_name
                    if script_name[0] != '/':
                        return script_name
                    else:
                        print('why folder in script selection?')


            self.screen.fill((30, 30, 60))
            for button in buttons:
                button.draw(self.screen)
            pygame.display.update()
            self.clock.tick(60)





launcher = Launcher()

pygame.display.update()
while launcher.run:
    folder = launcher.launch_type_menu_loop()
    game = launcher.select_script_loop(folder)

    vf_reset = False
    memory_i_inc = False
    clipping = True
    shifting = True
    jumping = True

    cpu = CPU(vf_reset, memory_i_inc, clipping, shifting, jumping, launcher.screen)
    cpu.load_rom(os.path.join(folder, game))
    while cpu.run:
        cpu.main_loop(launcher.clock)



pygame.quit()
'''
cpu.load_rom('games/BRIX')

clock = pygame.time.Clock()
while cpu.run:
    cpu.main_loop(clock)
'''