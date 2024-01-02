import os
import pygit2
from pygit2 import Repository


class MergeConflict(Exception):
    pass


class OriginNotFound(Exception):
    pass


# class NaevPMRemoteCallbacks(git.RemoteCallbacks):
#     def transfer_progress(self, stats):
#         print(
#             f'Cloning... {stats.indexed_objects} of {stats.total_objects} objects so far')
# TODO clone progress

def is_local_update_available(repo: Repository, remote_name='origin', branch='main'):
    for remote in repo.remotes:
        if remote.name == remote_name:
            # Current local commit:
            current = repo.lookup_reference(f'refs/heads/{branch}').target
            # Latest remote commit:
            latest = repo.lookup_reference(f'refs/remotes/{remote_name}/{branch}').target

            return current != latest
    raise OriginNotFound(f"Could not find git origin '{remote_name}' to check for updates.")


def fetch_latest_commit(repo: Repository, remote_name: str):
    for remote in repo.remotes:
        if remote.name == remote_name:
            # Fetch only the latest commit
            remote.fetch(depth=1)
            return
    raise OriginNotFound(f"Could not find git origin '{remote_name}' to fetch last commit")


def is_remote_and_local_commit_same(repo: pygit2.Repository, remote_name: str, branch: str):
    # Current local commit:
    current = repo.lookup_reference(f'refs/heads/{branch}').target
    # Latest (local) remote commit:
    latest = repo.lookup_reference(f'refs/remotes/{remote_name}/{branch}').target
    return current == latest


def git_repository_pull(repo: Repository, remote_name: str, branch: str):
    """
    Taken from <https://github.com/MichaelBoselowitz/pygit2-examples/blob/master/examples.py>
    """
    for remote in repo.remotes:
        if remote.name == remote_name:
            remote.fetch()
            remote_master_id = repo.lookup_reference(f'refs/remotes/{remote_name}/{branch}').target
            merge_result, _ = repo.merge_analysis(remote_master_id)
            # Up to date, do nothing
            if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                return
            # We can just fastforward
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
                repo.checkout_tree(repo.get(remote_master_id))
                try:
                    master_ref = repo.lookup_reference('refs/heads/%s' % branch)
                    master_ref.set_target(remote_master_id)
                except KeyError:
                    repo.create_branch(branch, repo.get(remote_master_id))
                repo.head.set_target(remote_master_id)
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
                raise MergeConflict("Pulling remote changes leads to a conflict")
                # repo.merge(remote_master_id)
                #
                # if repo.index.conflicts is not None:
                #     for conflict in repo.index.conflicts:
                #         print('Fatal: conflicts found in:'+conflict[0].path)
                #     raise AssertionError('Please resolve the conflict')
                #
                # user = repo.default_signature
                # tree = repo.index.write_tree()
                # commit = repo.create_commit('HEAD',
                #                             user,
                #                             user,
                #                             'Merge!',
                #                             tree,
                #                             [repo.head.target, remote_master_id])
                # # We need to do this or git CLI will think we are still merging.
                # repo.state_cleanup()
            else:
                raise AssertionError('Unknown merge analysis result')


class MyRemoteCallbacks(pygit2.RemoteCallbacks):

    def transfer_progress(self, stats):
        print(f'{stats.indexed_objects}/{stats.total_objects}')

    def sideband_progress(self, string):
        super().sideband_progress(string)
        print(string)

    def credentials(self, url, username_from_url, allowed_types):
        print(url, username_from_url, allowed_types)
        return super().credentials(url, username_from_url, allowed_types)

    def certificate_check(self, certificate, valid, host):
        print(certificate, valid, host)
        return super().certificate_check(certificate, valid, host)

    def update_tips(self, refname, old, new):
        super().update_tips(refname, old, new)
        print(refname, old, new)

    def push_update_reference(self, refname, message):
        super().push_update_reference(refname, message)
        print(refname, message)


def sync_repo(source: str, target: str, remote_name: str, branch: str):
    if os.path.exists(target):
        repo = pygit2.Repository(target)
        git_repository_pull(repo, remote_name=remote_name, branch=branch)
    else:
        pygit2.clone_repository(source, target, checkout_branch=branch,
                                callbacks=MyRemoteCallbacks(), depth=1)
