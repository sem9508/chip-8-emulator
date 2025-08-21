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

        self.font = pygame.font.SysFont('fixed sys', 32)
        self.text_surface = self.font.render(self.text, True, self.txt_color)


    def draw(self, screen:pygame.surface.Surface, offset_y):
        pygame.draw.rect(screen, self.current_color, (self.rect.x, self.rect.y+offset_y, self.rect.width, self.rect.height))
        screen.blit(self.text_surface, (self.rect.x + self.rect.width / 2 - self.text_surface.get_width()/2, self.rect.y + self.rect.height / 2 - self.text_surface.get_height()/2 + offset_y))

    def update(self, mouse, mouse_click, button_offset):
        if pygame.Rect(self.rect.x, self.rect.y+button_offset, self.rect.width, self.rect.height).collidepoint(mouse[0], mouse[1]):
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

        games_button = Button(20, 20, self.screen_width-40, self.screen_height/2-30, 'Games', (10, 10, 40), (0, 255, 220), (0, 0, 30), '/games')
        tests_button = Button(20, 40+self.screen_height/2-30, self.screen_width-40, self.screen_height/2-30, 'Tests', (10, 10, 40), (0, 255, 220), (0, 0, 30), '/tests')
        
        buttons.append(games_button)
        buttons.append(tests_button)

        button_offset = 0

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

            for button in buttons:
                if button.update(pygame.mouse.get_pos(), mouse_clicked, button_offset):
                    script_name = button.script_name
                    if script_name[0] == '/':
                        return script_name[1:]
                    else:
                        print('why script in menu?')

            self.screen.fill((30, 30, 60))
            for button in buttons:
                button.draw(self.screen, button_offset)
            pygame.display.update()
            self.clock.tick(60)

    def select_script_loop(self, folder):
        buttons = []
        i = 0
        margin = 20
        margin_between_buttons = 10

        button_offset = 0
        loop_run = True

        for f in os.listdir(folder):
            if os.path.isfile(os.path.join(folder, f)):
                if i % 2 == 0: # EVEN
                    x = margin
                    height = 50
                    y = margin + i/2*height + i*margin_between_buttons/2
                    width = (self.screen_width - margin*2)/2 - margin_between_buttons/2
                else: # ODD
                    width = (self.screen_width - margin*2)/2 - margin_between_buttons/2
                    x = self.screen_width - width - margin
                    y = margin + (i-1)/2*height + (i-1)*margin_between_buttons/2
                    height = 50
                    
                buttons.append(Button(x, y, width, height, f, (10, 10, 40), (0, 255, 220), (0, 0, 30), f))

                i += 1


        mouse_clicked = False
        while loop_run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    loop_run = False
                    break

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_clicked = True
                if event.type == pygame.MOUSEBUTTONUP:
                    mouse_clicked = False

                if event.type == pygame.MOUSEWHEEL:
                    button_offset += event.y*30
                    if button_offset > 0:
                        button_offset = 0


            for button in buttons:
                if button.update(pygame.mouse.get_pos(), mouse_clicked, button_offset):
                    script_name = button.script_name
                    if script_name[0] != '/':
                        return script_name
                    else:
                        print('why folder in script selection?')


            self.screen.fill((30, 30, 60))
            for button in buttons:
                button.draw(self.screen, button_offset)
            pygame.display.update()
            self.clock.tick(60)

launcher = Launcher()

pygame.display.update()
while launcher.run:
    folder = launcher.launch_type_menu_loop()
    if folder == None:
        continue
    game = launcher.select_script_loop(folder)

    if game == None:
        continue

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
