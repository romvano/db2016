SELECT * FROM Followee WHERE name = "example2@mail.ru";
SELECT * FROM Forum WHERE short_name= forum1;
SELECT * FROM Post WHERE id= -42;
SELECT * FROM Post p 
  LEFT JOIN Forum f ON p.forum = f.short_name 
  LEFT JOIN Thread t ON p.thread = t.id
  WHERE p.forum = 'forum1' AND p.date >= "2014-01-01 00:00:00" 
  ORDER BY p.date DESC ;
SELECT * FROM Post p 
  LEFT JOIN Forum f ON p.forum = f.short_name 
  LEFT JOIN Thread t ON p.thread = t.id
  WHERE p.forum = 'forumwithsufficientlylargename' AND p.date >= "2014-01-02 00:00:00" 
  ORDER BY p.date ASC 
  LIMIT 2 ;
SELECT * FROM Post p 
  LEFT JOIN Forum f ON p.forum = f.short_name
  WHERE p.forum = 'forum3' AND p.date >= "2014-01-03 00:00:00" 
  ORDER BY p.date DESC 
  LIMIT 3 ;
SELECT * FROM Post p 
  LEFT JOIN Forum f ON p.forum = f.short_name
  WHERE p.user = 'example2@mail.ru' AND p.date >= "2014-01-01 00:00:00" 
  ORDER BY p.date ASC ;
SELECT * FROM Post p 
  LEFT JOIN Thread t ON p.thread = t.id
  WHERE p.thread = '1' AND p.date >= "2014-01-03 00:00:00" 
  ORDER BY p.date DESC 
  LIMIT 3 ;
SELECT * FROM Post p 
  LEFT JOIN Thread t ON p.thread = t.id
  WHERE p.thread = '3' 
  ORDER BY p.date DESC ;
SELECT * FROM Subscription WHERE name = example2@mail.ru;
SELECT * FROM Thread WHERE id= 1;
SELECT * FROM Thread t 
  LEFT JOIN Forum f ON t.forum = f.short_name
  WHERE t.forum = 'forum1' AND t.date >= "2013-12-31 00:00:00" 
  ORDER BY t.date DESC;
SELECT * FROM Thread t 
  LEFT JOIN Forum f ON t.forum = f.short_name
  WHERE t.user = 'example3@mail.ru' AND t.date >= "2014-01-03 00:00:00" 
  ORDER BY t.date DESC 
  LIMIT 3 ;
SELECT * FROM Thread t 
  LEFT JOIN User u ON t.user = u.email 
  LEFT JOIN Followee fe ON t.user = fe.name 
  LEFT JOIN Follower fr ON t.user = fr.name 
  LEFT JOIN Subscription s ON t.user = s.name
  WHERE t.forum = 'forum2' AND t.date >= "2014-01-01 00:00:00" 
  GROUP BY t.id 
  ORDER BY t.date DESC;
SELECT * FROM Thread t 
  LEFT JOIN User u ON t.user = u.email 
  LEFT JOIN Forum f ON t.forum = f.short_name 
  LEFT JOIN Followee fe ON t.user = fe.name 
  LEFT JOIN Follower fr ON t.user = fr.name 
  LEFT JOIN Subscription s ON t.user = s.name
  WHERE t.forum = 'forumwithsufficientlylargename' AND t.date >= "2013-12-30 00:00:00" 
  GROUP BY t.id 
  ORDER BY t.date ASC 
  LIMIT 2 ;
SELECT * FROM User WHERE email= example2@mail.ru;
SELECT * FROM User u 
  LEFT JOIN Followee t ON u.email = t.follower 
  LEFT JOIN Followee fe ON u.email = fe.name 
  LEFT JOIN Follower fr ON u.email = fr.name 
  LEFT JOIN Subscription s ON u.email = s.name
  WHERE t.name = 'example3@mail.ru' AND u.id >= 0 
  GROUP BY u.email 
  ORDER BY u.name DESC 
  LIMIT 3 ;
SELECT * FROM User u 
  LEFT JOIN Followee t ON u.email = t.follower 
  LEFT JOIN Followee fe ON u.email = fe.name 
  LEFT JOIN Follower fr ON u.email = fr.name 
  LEFT JOIN Subscription s ON u.email = s.name
  WHERE t.name = 'example@mail.ru' 
  GROUP BY u.email 
  ORDER BY u.name ASC;
SELECT * FROM User u 
  LEFT JOIN Follower t ON u.email = t.followee 
  LEFT JOIN Followee fe ON u.email = fe.name 
  LEFT JOIN Follower fr ON u.email = fr.name 
  LEFT JOIN Subscription s ON u.email = s.name
  WHERE t.name = 'example3@mail.ru' AND u.id >= 1 
  GROUP BY u.email 
  ORDER BY u.name DESC 
  LIMIT 3 ;
SELECT * FROM User u 
  LEFT JOIN Follower t ON u.email = t.followee 
  LEFT JOIN Followee fe ON u.email = fe.name 
  LEFT JOIN Follower fr ON u.email = fr.name 
  LEFT JOIN Subscription s ON u.email = s.name
  WHERE t.name = 'example@mail.ru' 
  GROUP BY u.email 
  ORDER BY u.name ASC;
SELECT * FROM User u 
  LEFT JOIN Post t ON u.email = t.user 
  LEFT JOIN Followee fe ON u.email = fe.name 
  LEFT JOIN Follower fr ON u.email = fr.name 
  LEFT JOIN Subscription s ON u.email = s.name
  WHERE t.forum = 'forum1' 
  GROUP BY u.email 
  ORDER BY u.name DESC;
SELECT * FROM User u 
  LEFT JOIN Post t ON u.email = t.user 
  LEFT JOIN Followee fe ON u.email = fe.name 
  LEFT JOIN Follower fr ON u.email = fr.name 
  LEFT JOIN Subscription s ON u.email = s.name
  WHERE t.forum = 'forumwithsufficientlylargename' AND u.id >= 2 
  GROUP BY u.email 
  ORDER BY u.name ASC 
  LIMIT 2 ;
SELECT * FROM Post p
  LEFT JOIN Thread t ON p.thread = t.id
  WHERE p.thread = '4' AND p.date >= "2014-01-02 00:00:00"
  ORDER BY p.date ASC
  LIMIT 2 ;
SELECT * FROM Post p
  LEFT JOIN Thread t ON p.thread = t.id
  LEFT JOIN PostHierarchy ph ON p.id = ph.post
  WHERE p.thread = '2' AND p.date >= "2014-01-01 00:00:00"
  ORDER BY ph.parent DESC, ph.address ASC
  LIMIT 3 ;
SELECT * FROM Post p
  LEFT JOIN Thread t ON p.thread = t.id
  LEFT JOIN PostHierarchy ph ON p.id = ph.post
  WHERE ph.parent IN (
    SELECT parent FROM (
      SELECT * FROM Post p
        LEFT JOIN PostHierarchy ph ON p.id = ph.post
        WHERE p.thread = '4' AND p.date >= "2014-01-01 00:00:00"
        ORDER BY ph.parent ASC
        LIMIT 2
      ) a
    ) ORDER BY ph.parent ASC , ph.address;
