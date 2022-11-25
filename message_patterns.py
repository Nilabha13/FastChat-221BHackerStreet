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


def burst_messages(N, mu, sigma, K, delta_t, images_possible=False, images_prob=0.1):
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
        num_peers = max(min(round(random.gauss(mu, sigma)), N-1), 1)
        sender_idx = random.randrange(N)
        receivers_possible = list(range(N)); receivers_possible.remove(sender_idx)
        receivers_idx = random.sample(receivers_possible, num_peers)
        for receiver_idx in receivers_idx:
            is_image = False
            if images_possible and random.random() <= images_prob:
                is_image = True
            patterns.append((sender_idx, receiver_idx, delta_t, is_image))
    return patterns


def heavyweight_users(N, delta_t, M=5, images_possible=False, images_prob=0.1):
    """This is one of the messaging patterns used during performance analysis.
    This simulates choosing clients in skip intervals of the number of servers to send data. Then each such client sends a message to all other clients in the network.
    This would sharply increase the load on a particular server if certain load-balancing strategies are used.
    Even if a resilient load-balancing strategy is used, it still puts a lot of load on the server because of the sheer number of messages beings sent.

    :param N: The number of clients in the network
    :type N: int
    :param delta_t: The time delay between two messages being sent
    :type delta_t: int / float
    :param M: The number of servers in the network, defaults to 5
    :type M: int, optional
    :param images_possible: Could images be sent, defaults to False
    :type images_possible: bool, optional
    :param images_prob: If images can be sent, the probability of sending an image, defaults to 0.1
    :type images_prob: float, optional
    :return: The pattern of messages to be sent
    :rtype: list
    """
    patterns = []
    for sender_idx in range(0, N, M):
        receivers_idx = list(range(N)); receivers_idx.remove(sender_idx)
        for receiver_idx in receivers_idx:
            is_image = False
            if images_possible and random.random() <= images_prob:
                is_image = True
            patterns.append((sender_idx, receiver_idx, delta_t, is_image))
    return patterns


def exponential_time_delay_groups(num_groups, num_members, mu, K, images_possible=False, images_prob=0.1):
    """This is one of the group messaging patterns used during performance analysis.
    This simulates the sending of messages from a random user in a random group with an exponential time delay between two messages with the exponential parameter mu.
    K such messages are sent across the network.

    :param num_groups: The number of groups in the network
    :type num_groups: int
    :param num_members: The number of group members per group
    :type num_members: int
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
        group_idx = random.randrange(num_groups)
        member_idx = random.randrange(num_members)
        delay = random.expovariate(mu)
        is_image = False
        if images_possible and random.random() <= images_prob:
            is_image = True
        patterns.append((group_idx, member_idx, delay, is_image))
    return patterns


def fake_exponential_time_delay_groups(num_groups, num_members, mu, K, min_time, images_possible=False, images_prob=0.1):
    """This is one of the group messaging patterns used during performance analysis.
    This simulates the sending of messages from a random user in a random group with an exponential time delay between two messages with the exponential parameter mu.
    K such messages are sent across the network.
    It is also ensured that the time delay is above a certain minimum threshold.

    :param num_groups: The number of groups in the network
    :type num_groups: int
    :param num_members: The number of group members per group
    :type num_members: int
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
        group_idx = random.randrange(num_groups)
        member_idx = random.randrange(num_members)
        delay = max(random.expovariate(mu), min_time)
        is_image = False
        if images_possible and random.random() <= images_prob:
            is_image = True
        patterns.append((group_idx, member_idx, delay, is_image))
    return patterns


def groups_transversal(num_groups, num_members, K, delta_t, images_possible=False, images_prob=0.1):
    """This is one of the group messaging patterns used during performance analysis.
    This simulates sequentially going through each group, choosing a random user and making them send a message. The messages are sent after a delay of delta_t.
    K such passes through all the groups are performed.

    :param num_groups: The number of groups in the network
    :type num_groups: int
    :param num_members: The number of group memebers per group
    :type num_members: int
    :param K: The number of passes through all the groups
    :type K: int
    :param delta_t: The time delay between two messages being sent
    :type delta_t: int / float
    :param images_possible: Could images be sent, defaults to False
    :type images_possible: bool, optional
    :param images_prob: If images can be sent, the probability of sending an image, defaults to 0.1
    :type images_prob: float, optional
    :return: The pattern of messages to be sent
    :rtype: list
    """
    patterns = []
    for l in range(K):
        for group_idx in range(num_groups):
            member_idx = random.randrange(num_members)
            is_image = False
            if images_possible and random.random() <= images_prob:
                is_image = True
            patterns.append((group_idx, member_idx, delta_t, is_image))
    return patterns


def group_creation_sample(num_members, shift, num_groups):
    """ This process creates a generalized set of groups for the system. Assumption is that every group has atleast 3 users in these general test
    groups. Groups are created as: first group goes from member 0 to member N-1. Second from member k to k+N-1, third from 2k to 2k+N-1 etc. We
    create k groups of this type. This allows for testing all sorts of general, overlapping groups. N is num_members, k is shift. The function 
    returns the names of members and admins for the groups in a list

    :param num_members: number of members in group
    :type num_members: int
    :param shift: shift between adjacent groups
    :type shift: int
    :param num_groups: number of groups in system
    :type num_groups: int
    :return: list of tuples of form (admin number, tuple of member numbers, group name)
    :rtype: tuple
    """
    l = []
    for i in range(num_groups):
        member_tuple = range(i*shift,i*shift+num_members)
        admin = member_tuple[2]
        g_name = f"g{i}"
        l.append((admin, member_tuple, g_name))
    return l