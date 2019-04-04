from app import app
from service import *
# this file is for modifying articles to be hidden or delete articles and comments
if __name__ == '__main__':
    with app.app_context():
        print('using man for help, or input your command:')
        while True:
            command = input()
            if command == 'man':
                print('input hide article <article_id> for hiding an article')
                print('input show article <article_id> for showing an article')
                print('input del article <article_id> for deleting an article')
                print('input del comment <comment_id> for deleting a comment')
                continue
            else:
                split = command.split()
                if len(split) != 3:
                    print('There are some error on your command, try to use man to get help')
                    continue
                else:
                    if split[0] == 'hide':
                        article = article_service.find_by_id(split[2])
                        if article is None:
                            print('Article with this id does not exist')
                            continue
                        article_service.set_hidden(article, 1)
                        print('hide successfully')
                    elif split[0] == 'show':
                        article = article_service.find_by_id(split[2])
                        if article is None:
                            print('Article with this id does not exist')
                            continue
                        article_service.set_hidden(article, 0)
                        print('show successfully')
                    elif split[0] == 'del':
                        if split[1] == 'article':
                            article = article_service.find_by_id(split[2])
                            if article is None:
                                print('Article with this id does not exist')
                                continue
                            article_service.delete(article)
                            print('delete successfully')
                        elif split[1] == 'comment':
                            comment = comment_service.find_by_id(split[2])
                            if comment is None:
                                print('Comment with this id does not exist')
                                continue
                            comment_service.delete(comment)
                            print('delete successfully')
                        else:
                            print('There are some error on your command, try to use man to get help')
                            continue
                    else:
                        print('There are some error on your command, try to use man to get help')
                        continue
