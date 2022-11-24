import random

def exponential_time_delay(N, mu, K, images_possible=False, images_prob=0.1):
    patterns = []
    for k in range(K):
        sender_idx, receiver_idx = random.sample(range(N), 2)
        delay = random.expovariate(mu)
        is_image = False
        if images_possible and random.random() <= images_prob:
            is_image = True
        patterns.append((sender_idx, receiver_idx, delay, is_image))


def i_only_talk_to_bestie(N, mu, sigma, K, delta_t, images_possible=False, images_prob=0.1):
    patterns = []
    for k in range(K):
        num_besties = max(min(round(random.gauss(mu, sigma)), N-1), 1)
        sender_idx = random.randrange(N)
        receivers_possible = list(range(N)); receivers_possible.remove(sender_idx)
        receivers_idx = random.sample(receivers_possible, num_besties)
        for idx, receiver_idx in enumerate(receivers_idx):
            is_image = False
            if images_possible and random.random() <= images_prob:
                is_image = True
            if idx == 0:
                patterns.append((sender_idx, receiver_idx, delta_t, is_image))
            else:
                patterns.append((sender_idx, receiver_idx, 0, is_image))
        