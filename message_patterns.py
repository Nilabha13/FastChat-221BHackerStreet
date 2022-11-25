import random

def exponential_time_delay(N, mu, K, images_possible=False, images_prob=0.1):
    """This is one of the messaging patterns used during performance analysis.
    This simulates the sending of messages from a random user to another random user with an exponential time delay between two messages with the exponential parameter mu.
    K such messages are sent across the network.

    :param N: The number of clients in the network
    :type N: int
    :param mu: The parameter of the exponential distribution
    :type mu: int / float
    :param K: The number of messages to be sent across the network
    :type K: int
    :param images_possible: Could images be sent, defaults to False
    :type images_possible: bool, optional
    :param images_prob: If images can be sent, the probability of sending an image, defaults to 0.1
    :type images_prob: float, optional
    :return: The pattern of messages to be sent
    :rtype: list
    """
    patterns = []
    for k in range(K):
        sender_idx, receiver_idx = random.sample(range(N), 2)
        delay = random.expovariate(mu)
        is_image = False
        if images_possible and random.random() <= images_prob:
            is_image = True
        patterns.append((sender_idx, receiver_idx, delay, is_image))
    return patterns


def fake_exponential_time_delay(N, mu, K, min_time, images_possible=False, images_prob=0.1):
    """This is one of the messaging patterns used during performance analysis.
    This simulates the sending of messages from a random user to another random user with an exponential time delay between two messages with the exponential parameter mu.
    K such messages are sent across the network.
    It is also ensured that the time delay is above a certain minimum threshold.

    :param N: The number of clients in the network
    :type N: int
    :param mu: The parameter of the exponential distribution
    :type mu: int / float
    :param K: The number of messages to be sent across the network
    :type K: int
    :param min_time: The threshold minimum time delay between two messages being sent
    :type min_time: float
    :param images_possible: Could images be sent, defaults to False
    :type images_possible: bool, optional
    :param images_prob: If images can be sent, the probability of sending an image, defaults to 0.1
    :type images_prob: float, optional
    :return: The pattern of messages to be sent
    :rtype: list
    """
    patterns = []
    for k in range(K):
        sender_idx, receiver_idx = random.sample(range(N), 2)
        delay = random.expovariate(mu)
        if(delay<min_time):
            delay=min_time
        is_image = False
        if images_possible and random.random() <= images_prob:
            is_image = True
        patterns.append((sender_idx, receiver_idx, delay, is_image))
    return patterns


def i_only_talk_to_bestie(N, mu, sigma, K, delta_t, images_possible=False, images_prob=0.1):
    """This is one of the messaging patterns used during performance analysis.
    This simulates a random user sending messages to a number of other users distributed according to a truncated discrete Gaussian with mean mu and standard deviation sigma.
    K such random users are chosen and this process is repeated K times, with a time delay of delta_t between each such process.

    :param N: The number of clients in the network
    :type N: int
    :param mu: The mean of the discrete Gaussian
    :type mu: int / float
    :param sigma: The standard deviation of the discrete Gaussian
    :type sigma: int / float
    :param K: The number of times the process is to be repeated
    :type K: int
    :param delta_t: The time delay between each execution of the process
    :type delta_t: int / float
    :param images_possible: Could images be sent, defaults to False
    :type images_possible: bool, optional
    :param images_prob: If images can be sent, the probability of sending an image, defaults to 0.1
    :type images_prob: float, optional
    :return: The pattern of messages to be sent
    :rtype: list
    """
    patterns = []
    for k in range(K):
        num_besties = max(min(round(random.gauss(mu, sigma)), N-1), 1)
        sender_idx = random.randrange(N)
        receivers_possible = list(range(N)); receivers_possible.remove(sender_idx)
        receivers_idx = random.sample(receivers_possible, num_besties)
        for receiver_idx in receivers_idx:
            is_image = False
            if images_possible and random.random() <= images_prob:
                is_image = True
            patterns.append((sender_idx, receiver_idx, delta_t, is_image))
    return patterns


def heavyweight_users(N, M=5, images_possible=False, images_prob=0.1):
    patterns = []
    for sender_idx in range(0, N, M):
        receivers_idx = list(range(N)); receivers_idx.remove(sender_idx)
        for receiver_idx in receivers_idx:
            is_image = False
            if images_possible and random.random() <= images_prob:
                is_image = True
            patterns.append((sender_idx, receiver_idx, 0, is_image))
    return patterns


def exponential_time_delay_groups(num_groups, num_members, mu, K, images_possible=False, images_prob=0.1):
    patterns = []
    for k in range(K):
        group_idx = random.randrange(num_groups)
        member_idx = random.randrange(num_members)
        delay = random.expovariate(mu)
        is_image = False
        if images_possible and random.random() <= images_prob:
            is_image = True
        patterns.append((group_idx, member_idx, delay, is_image))
    return patterns


def fake_exponential_time_delay_groups(num_groups, num_members, mu, K, min_time, images_possible=False, images_prob=0.1):
    patterns = []
    for k in range(K):
        group_idx = random.randrange(num_groups)
        member_idx = random.randrange(num_members)
        delay = max(random.expovariate(mu), min_time)
        is_image = False
        if images_possible and random.random() <= images_prob:
            is_image = True
        patterns.append((group_idx, member_idx, delay, is_image))
    return patterns


def groups_transversal(num_groups, num_members, K, delta_t, images_possible=False, images_prob=0.1):
    patterns = []
    for l in range(K):
        for group_idx in range(num_groups):
            member_idx = random.randrange(num_members)
            is_image = False
            if images_possible and random.random() <= images_prob:
                is_image = True
            patterns.append((group_idx, member_idx, delta_t, is_image))
    return patterns




def group_creation_sample(num_members, overlap, num_groups):
    l = []
    for i in range(num_groups):
        member_tuple = range(i*overlap,i*overlap+num_members)
        admin = member_tuple[2]
        g_name = f"g{i}"
        l.append((admin, member_tuple, g_name))
    return l